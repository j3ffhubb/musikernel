/* This file is part of the libshds project, copyright Jeff Hubbard
 *
 * See https://github.com/j3ffhubb/libshds/blob/master/LICENSE
 * for licensing details */

#ifndef LIBSHDS_H
#define LIBSHDS_H

/* Members with a leading underscore are considered private.
 *
 * See tests.c for examples of using the various structs and
 * functions */

#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#define SHDS_MAJOR_VERSION 1
#define SHDS_MINOR_VERSION 2

/* Comparison function for sorting algorithms
 *
 * Use 'less than' for ascending sorts and 'greater than' for descending
 *
 * @return 1 for true, or 0 for false */
typedef int (*shds_cmpfunc)(void*, void*);

/* Comparison function for determing less-than/equal/greater-than
 *
 * @return -1 for 'less than', 0 for 'equal' or 1 for 'greater than' */
typedef int (*shds_eqfunc)(void*, void*);

/* Destructor for freeing the memory of an object in a data structure.
 *
 * Pass a NULL pointer to not free the memory, pass 'free',
 * or a custom function */
typedef void (*shds_dtor)(void*);

/* Custom memory allocator.  Given that libshds is a single-header library
 * that is platform-agnostic, implementing a custom memory allocator is
 * an exercise left to the user, this simply wraps malloc by default for
 * maximum portability.
 *
 * Possible optimizations are allocating aligned memory using
 * posix_memalign, or using mmap to allocate hugepages
 *
 * @size The size of the memory to allocate in bytes */
void * shds_alloc(size_t size)
{
    return malloc(size);
}

/* This is to realloc as shds_alloc is to malloc
 *
 * @data The existing pointer to reallocate
 * @size The size of the memory to allocate in bytes */
void * shds_realloc(void *data, size_t size)
{
    return realloc(data, size);
}



/* Complement to shds_alloc.  It simply wraps 'free' by default, but can
 * be replaced for instances where that isn't appropriate, such as
 * implementations of shds_alloc that use mmap to allocate hugepages.
 *
 * @ptr A pointer to the memory to be freed */
void shds_free(void *ptr)
{
    free(ptr);
}

/* Generic array slice calculation, used by various data structures
 *
 * Intended to be simlar to python[3:-1:2] slice syntax */
struct _shds_slice {
    /* Start index  */
    size_t start;
    /* End index */
    size_t end;
    /* Step size, ie: 2 means skip every other item */
    size_t step_size;
    /* The length of the new data structure */
    size_t len;
};

/* Private function for calculating slices, similar to Python slices
 *
 * @value     The array index, it can be < 0 or > array_len
 * @array_len The length of the containing array *
 * @return    The wrapped array index */
size_t _shds_slice_wrap(int64_t value, size_t array_len)
{
    int64_t result;

    if(value < 0)
    {
        result = array_len + value;
        if(result < 0)
            result = 0;
    }
    else if(value > array_len)
    {
        result = array_len;
    }
    else
    {
        result = value;
    }

    return (size_t)result;
}

/* Private function for generating full slice data
 *
 * @start     The starting array index
 * @end       The end array index
 * @step_size 1 to capture every element from start to end,
 *            2 for every other, etc...
 * @array_len The length of the containing array */
struct _shds_slice shds_slice(int64_t start, int64_t end,
    int64_t step_size, size_t array_len)
{
    assert(step_size != 0);
    struct _shds_slice result;
    result.start = _shds_slice_wrap(start, array_len);
    result.end = _shds_slice_wrap(end, array_len);
    result.step_size = step_size;

    int64_t len = result.end - result.start;

    if(step_size < 0)
    {
        step_size *= -1;
    }

    if(len < 0)
    {
        len = 0;
    }
    else /* Ceiling division */
    {
        len = len / step_size + (len % step_size != 0);
    }

    result.len = len;

    return result;
}

/* A generic object data structure.
 *
 * You are not forced to use this
 * for the values passed to data structures, but it can be useful for
 * implementing garbage collection and generic programming, at a slight
 * performance and memory cost */
struct ShdsObject {
    /* pointer to the data this object represents */
    void * value;
    /* reference count for garbage collection,
     * functions with _o suffixes increment this, a shds_object_dtor
     * will decrement this.  You may also need to manually
     * increment or call shds_object_dtor if using objects in
     * your data structures and functions */
    uint32_t ref_count;
    /* user-defined type, it's use is optional */
    uint32_t type;
    /* function to free the memory of ->value
     *
     * You should pass shds_object_dtor to the containing data structure */
    shds_dtor dtor;
};

/* The constructor for a new object
 *
 * @value A pointer to the value this object holds
 * @type  A user-defined type to allow correlating to a type, pass 0 to not use
 * @dtor  A destructor function to free ->value */
struct ShdsObject *shds_object_new(void * value,
    uint32_t type, shds_dtor dtor)
{
    struct ShdsObject *result =
        (struct ShdsObject*)shds_alloc(sizeof(struct ShdsObject));
    result->value = value;
    result->ref_count = 0;
    result->type = type;
    result->dtor = dtor;
    return result;
}

/* Object destructor with reference counting and garbage collection
 *
 * If using objects in a data structure, specify this in the data
 * structures constructor, and it will call the object's own
 * destructor function and decrement the reference count
 *
 * @object A pointer to a struct ShdsObject */
void shds_object_dtor(void *object)
{
    struct ShdsObject *self = (struct ShdsObject*)object;
    --self->ref_count;

    if(!self->ref_count && self->dtor)
    {
        self->dtor(self->value);
        shds_free(self);
    }
}

/* List data structure implementation */
struct ShdsList {
    /* A dynamic array of void* pointers to the items in the list */
    void **data;
    /* The current length of the list */
    size_t len;
    /* The size of ->data, the list will be grown if ->len exceeds this */
    size_t max_size;
    /* The function used to free values, or NULL to not free values */
    shds_dtor dtor;
};

/* The constructor for the list data structure
 *
 * @default_size The initial maximum size of the list length will be zero
 * @dtor         The destructor to call on the stored values when
 *               freeing the list
 */
struct ShdsList * shds_list_new(size_t default_size, shds_dtor dtor)
{
    struct ShdsList * result =
        (struct ShdsList*)shds_alloc(sizeof(struct ShdsList));
    result->dtor = dtor;
    result->max_size = default_size;
    result->len = 0;
    result->data = (void**)shds_alloc(sizeof(void*) * default_size);
    return result;
}

/* Create a shallow copy of a list in O(n) */
struct ShdsList * shds_list_copy(struct ShdsList * self)
{
    size_t i;
    struct ShdsList * result = shds_list_new(self->max_size, self->dtor);
    result->len = self->len;

    for(i = 0; i < self->len; ++i)
    {
        result->data[i] = self->data[i];
    }

    return result;
}

/* Create a new list that is a slice of an existing list.
 *
 * Like in Python, the start/end indices can be negative numbers
 *
 * @start     The start index
 * @end       The end index
 * @step_size 1 to add each item from start to end, 2 for every other... */
struct ShdsList *shds_list_slice(struct ShdsList *self,
    int64_t start, int64_t end, int64_t step_size)
{
    size_t i = 0;
    size_t i2;
    struct _shds_slice slice = shds_slice(start, end, step_size, self->len);
    struct ShdsList *result = shds_list_new(slice.len, NULL);

    if(step_size > 0)
    {
        for(i2 = slice.start; i2 < slice.end; i2 += step_size)
        {
            result->data[i] = self->data[i2];
            ++i;
        }
    }
    else
    {
        for(i2 = slice.end; i2 >= slice.start; i2 += step_size)
        {
            result->data[i] = self->data[i2];
            ++i;
        }
    }

    result->len = slice.len;
    return result;
}

/* @index  The zero-based index of the object you wish to retrieve
 * @return The object at [index] in O(1)  */
void * shds_list_index_get(struct ShdsList * self, size_t index)
{
    assert(index >= 0 && index < self->len && self->data[index]);
    return self->data[index];
}

/* Set the object at [index] to the value pointer in O(1) */
void shds_list_index_set(struct ShdsList * self, size_t index, void * value)
{
    assert(index >= 0 && index < self->len && self->data[index]);
    self->data[index] = value;
}

/* Grow a list by doubling the potential number of elements.
 *
 * This is called automatically by _append() */
void shds_list_grow(struct ShdsList * self)
{
    self->max_size *= 2;
    self->data = (void**)shds_realloc(
        self->data, sizeof(void*) * self->max_size);
}

/* Append an object to the end of the list in O(1),
 * with an amoritized worst-case of O(n) if the list must be grown */
void shds_list_append(struct ShdsList *self, void *value)
{
    if(self->len >= self->max_size)
    {
        shds_list_grow(self);
    }

    self->data[self->len] = value;
    ++self->len;
}

/* Object version of shds_list_append  */
void shds_list_append_o(struct ShdsList *self, struct ShdsObject *object)
{
    shds_list_append(self, object);
    object->ref_count++;
}

/* Free a list. */
void shds_list_free(struct ShdsList * self)
{
    if(self->dtor)
    {
        size_t i;
        for(i = 0; i < self->len; ++i)
        {
            self->dtor(self->data[i]);
        }
    }

    shds_free(self->data);
    shds_free(self);
}

/* Reverse the order of a list in-place
 *
 * @self The instance */
void shds_list_reverse(struct ShdsList *self)
{
    size_t i;
    size_t i2 = self->len - 1;
    size_t len = self->len / 2;
    void *swap;

    for(i = 0; i < len; ++i)
    {
        swap = self->data[i2];
        self->data[i2] = self->data[i];
        self->data[i] = swap;
        --i2;
    }
}

/* Remove any NULL pointers from a list
 *
 * There is intentionally no method to remove an item from the
 * middle of a list because that would scale at O(n), which would
 * perform very poorly if you had to make multiple calls with a
 * large list.  The intended use it to set the pointer to NULL and
 * check it when iterating ->data.
 *
 * This method can be used to defragment a list that has had
 * items removed by NULLing the pointer, for example, if you would
 * wanted to be able to sort the list */
void shds_list_compact(struct ShdsList * self)
{
    size_t i, i2;

    for(i = i2 = 0; i < self->len; ++i)
    {
        if(self->data[i])
        {
            self->data[i2] = self->data[i];
            ++i2;
        }
    }

    /* Set the unused pointers to NULL to ensure that they cannot be
     * accidentally referenced */

    for(i = i2; i < self->len; ++i)
    {
        self->data[i] = NULL;
    }

    self->len = i2;
}

/* Binary search a SORTED (ascending) list to find a value in O(log n)
 *
 * You must sort this list yourself before calling this function,
 * otherwise it will fail.
 *
 * @self The instance */
void * shds_list_bsearch(struct ShdsList *self,
    void * value, shds_eqfunc eqfunc)
{
    int cmp;

    /* corner-case for odd-numbered lengths */
    if(self->len % 2 && !eqfunc(value, self->data[self->len - 1]))
    {
        return self->data[self->len - 1];
    }

    int64_t i = 0;
    size_t part = self->len >> 1;

    while(part)
    {
        cmp = eqfunc(value, self->data[i]);

        if(cmp > 0)
        {
            i += part;
        }
        else if(cmp < 0)
        {
            i -= part;
        }
        else
        {
            return self->data[i];
        }
        /* Use '>> 1' instead of '/ 2' it should be as fast in instances
         * where the compiler figured out to do the same, and much faster
         * if the compiler did not figure out the optimization */
        part >>= 1;
    }

    if(i < self->len && i >= 0)
    {
        cmp = eqfunc(value, self->data[i]);
    }
    else
    {
        return NULL;
    }

    if(!cmp)
    {
        return self->data[i];
    }
    /* I've only observed this codepath being hit on very large lists
       or the item not being in the list */
    else if(cmp > 0)
    {
        ++i;
        while(cmp > 0 && i < self->len)
        {
            cmp = eqfunc(value, self->data[i]);
            if(!cmp)
                return self->data[i];
            ++i;
        }
    }
    else
    {
        --i;
        while(cmp < 0 && i >= 0)
        {
            cmp = eqfunc(value, self->data[i]);
            if(!cmp)
                return self->data[i];
            --i;
        }
    }

    return NULL;
}

/* Remove and return the last item from the list, like a LIFO/stack  */
void * shds_list_pop(struct ShdsList * self)
{
    if(!self->len)
    {
        return NULL;
    }
    else
    {
        --self->len;
        void * result = self->data[self->len];
        self->data[self->len] = NULL;
        return result;
    }
}

/* Private Merge Sort function, don't use this */
void _shds_list_msort(struct ShdsList * self, shds_cmpfunc cmpfunc,
    size_t low, size_t mid, size_t high, void **temp);
/* Private Merge Sort partitioning function, don't use this */
void _shds_list_msort_part(struct ShdsList * self,
    shds_cmpfunc cmpfunc, int low, int high, void **temp);

/* Merge Sort a list */
void shds_list_msort(struct ShdsList * self, shds_cmpfunc cmpfunc)
{
    void ** temp = (void**)shds_alloc(sizeof(void*) * self->len);
    _shds_list_msort_part(self, cmpfunc, 0, self->len - 1, temp);
    shds_free(temp);
}

void _shds_list_msort(struct ShdsList * self, shds_cmpfunc cmpfunc,
    size_t low, size_t mid, size_t high, void **temp)
{
    size_t i, m, k, l;
    void ** arr = self->data;

    l = low;
    m = mid + 1;

    for(i = low; (l <= mid) && (m <= high); ++i)
    {
         if(cmpfunc(arr[l], arr[m]))
         {
             temp[i] = arr[l];
             ++l;
         }
         else
         {
             temp[i] = arr[m];
             ++m;
         }
    }

    if(l > mid)
    {
         for(k = m; k <= high; ++k)
         {
             temp[i] = arr[k];
             ++i;
         }
    }
    else
    {
         for(k = l; k <= mid; ++k)
         {
             temp[i] = arr[k];
             ++i;
         }
    }

    for(k = low; k <= high; ++k)
    {
         arr[k] = temp[k];
    }
}

void _shds_list_msort_part(struct ShdsList * self,
    shds_cmpfunc cmpfunc, int low, int high, void **temp)
{
    size_t mid;

    if(low < high)
    {
         mid = (low + high) / 2;
         _shds_list_msort_part(self, cmpfunc, low, mid, temp);
         _shds_list_msort_part(self, cmpfunc, mid + 1, high, temp);
         _shds_list_msort(self, cmpfunc, low, mid, high, temp);
    }
}

/* Insertion Sort a list */
void shds_list_isort(struct ShdsList * self, shds_cmpfunc cmpfunc)
{
    size_t i;
    int64_t i2;
    void *swap;
    void **data = self->data;

    for(i = 1; i < self->len; ++i)
    {
        for(i2 = i; i2 > 0 && cmpfunc(data[i2], data[i2 - 1]); --i2)
        {
            swap = data[i2 - 1];
            data[i2 - 1] = data[i2];
            data[i2] = swap;
        }
    }
}

/* Generic function to sort a list, the algorithm may change in the future.
 *
 * cmpfunc: 'less than' to sort ascending, 'greater than' for descending */
void shds_list_sort(struct ShdsList * self, shds_cmpfunc cmpfunc)
{
    if(self->len < 200)
    {
        shds_list_isort(self, cmpfunc);
    }
    else
    {
        shds_list_msort(self, cmpfunc);
    }
}


/* A generic key/value pair struct */
struct ShdsKvp {
    /* The hash of char *key */
    uint64_t hash;
    /* The length of the key */
    size_t key_len;
    /* The key, it can be a string or generic binary data */
    char *key;
    /* A pointer to the value */
    void *value;
};

/* Used by the dictionary to store key/value pairs  */
struct Shdshash_bucket {
    /* The current count of items in this bucket */
    size_t count;
    /* The key/value pairs */
    struct ShdsKvp **data;
};

/* A dictionary data structure  */
struct ShdsDict {
    /* The the maximum length of an individual hash bucket,
     * if a bucket exceeds this length, shds_dict_grow is called  */
    size_t bucket_size;
    /* The size of shds_kvp **data */
    size_t size;
    /* The dictionary key/value pairs */
    struct Shdshash_bucket **data;
    /* The number of key/value pairs in the dictionary */
    size_t len;
    /* The function to call for freeing values or NULL to not free values*/
    shds_dtor dtor;
};

struct ShdsKvp *shds_dict_set(struct ShdsDict*, struct ShdsKvp*);
void shds_kvp_free(struct ShdsKvp*, shds_dtor dtor);

/* To use other data types as keys, cast them to char*
 *
 * If using char* as the key, calculate strlen() yourself and
 * pass it as size */
uint64_t shds_hash(char * data, size_t size)
{
    int i;
    uint64_t result = 0;

    for(i = 0; i < size; ++i)
    {
        result <<= 2;
        result += ((data[i] + i) * data[i]) + 1 + i;
        result >>= 1;
    }

    return result;
}

/* The constructor for a new hash bucket
 *
 * @bucket_size The maximum size of a bucket before growing the dictionary */
struct Shdshash_bucket * shds_hash_bucket_new(size_t bucket_size)
{
    assert(bucket_size >= 5 && bucket_size < 10000);
    struct Shdshash_bucket * result =
        (struct Shdshash_bucket*)shds_alloc(sizeof(struct Shdshash_bucket));
    result->count = 0;
    result->data =
        (struct ShdsKvp**)shds_alloc(sizeof(struct ShdsKvp*) * bucket_size);
    return result;
}

/* Free a hash bucket */
void shds_hash_bucket_free(struct Shdshash_bucket * self)
{
    shds_free(self->data);
    shds_free(self);
}

/* The constructor for a new dictionary.
 *
 * @default_size The initial size of the dictionary's data array.
 *               Growing the dictionary is an expensive operation, it's
 *               best to set this to a fairly large number if you are
 *               not memory-constrained.
 * @bucket_size  The maximum size of the hash bucket before growing
 *               the dictionary.  A good default size is 20.  The cost
 *               of a lookup is O(1), but larger bucket size settings can
 *               increase the computation time of a unit while further
 *               amoritizing the cost of growing the bucket.
 * */
struct ShdsDict * shds_dict_new(size_t default_size,
    size_t bucket_size, shds_dtor dtor)
{
    size_t i;
    struct ShdsDict * result =
        (struct ShdsDict*)shds_alloc(sizeof(struct ShdsDict));
    result->len = 0;
    result->bucket_size = bucket_size;
    result->size = default_size;
    result->data = (struct Shdshash_bucket**)shds_alloc(
        sizeof(struct Shdshash_bucket*) * result->size);
    result->dtor = dtor;

    for(i = 0; i < result->size; ++i)
    {
        result->data[i] = NULL;
    }

    return result;
}

/* Locate the index (or would-be index) of hash
 *
 * @hash The hash of the object calculated with shds_hash() */
size_t shds_hash_index(struct ShdsDict * self, uint64_t hash)
{
    return hash % self->size;
}

/* The constructor for a new key/value pair
 *
 * Keys are copied to the struct by value and hashed, values are by
 * reference and store only a pointer.
 *
 * If using this as a key to lookup a value in a dictionary, you can
 * simply specify NULL for the value argument
 *
 * @key      The data to use as the key.  If using something other than text
 *           as a key, cast it to char* first
 * @key_size The length of key in bytes.  Use strlen(...) to calculate
 *           if using char* data, otherwise sizeof()
 * @value    A pointer to the data, or NULL if this instance is only
 *           being used as a key
 */
struct ShdsKvp *shds_kvp_new(char *key, size_t key_size, void *value)
{
    struct ShdsKvp * result = (struct ShdsKvp*)shds_alloc(
        sizeof(struct ShdsKvp));
    result->key_len = key_size;
    result->key = (char*)shds_alloc(key_size);
    memcpy(result->key, key, key_size);
    result->value = value;
    result->hash = shds_hash(key, key_size);

    return result;
}

/* Grow a dictionary by doubling the size of it's ->data array
 *
 * This is called automatically when a hash collision is detected */
void shds_dict_grow(struct ShdsDict * self)
{
    size_t i, i2;
    size_t old_size = self->size;
    size_t old_len = self->len;

    self->size *= 2;
    struct Shdshash_bucket **old_data = self->data;
    self->data = (struct Shdshash_bucket**)shds_alloc(
        sizeof(struct Shdshash_bucket*) * self->size);

    struct Shdshash_bucket *bucket;
    struct ShdsKvp *kvp;

    for(i = 0; i < self->size; ++i)
    {
        self->data[i] = NULL;
    }

    for(i = 0; i < old_size; ++i)
    {
        bucket = old_data[i];
        if(bucket)
        {
            for(i2 = 0; i2 < bucket->count; ++i2)
            {
                kvp = bucket->data[i2];
                shds_dict_set(self, kvp);
            }

            shds_hash_bucket_free(bucket);
        }
    }

    self->len = old_len;
    shds_free(old_data);
}

/* Search the hash bucket for a key
 *
 * @self   The instance
 * @key    The key to lookup (you can specify NULL for the ->value)
 * @return The hash bucket index of key, or -1 if not found */
int shds_hash_bucket_pos(struct Shdshash_bucket *self, struct ShdsKvp *key)
{
    int i;
    struct ShdsKvp *current;

    for(i = 0; i < self->count; ++i)
    {
        current = self->data[i];
        /* memcmp is unlikely to ever be called unless it is the actual
         * key, so 1 (or occasionally 2) fast integer-type compares
         * per iteration and one memcmp for the entire search if
         * the key is found  */
        if(current->hash == key->hash &&
           current->key_len == key->key_len &&
           !memcmp(current->key, key->key, current->key_len))
        {
            return i;
        }
    }

    return -1;
}

/* Add or replace a key/value pair in the dictionary.
 *
 * @self   The instance
 * @kvp    A key/value pair to set
 * @return The old key/value pair's pointer (which you may then want
 *         to free), or NULL if the key was not in the dictionary */
struct ShdsKvp *shds_dict_set(struct ShdsDict * self, struct ShdsKvp * kvp)
{
    size_t i;
    struct ShdsKvp *result = NULL;
    size_t pos = shds_hash_index(self, kvp->hash);
    struct Shdshash_bucket *bucket = self->data[pos];

    if(bucket)
    {
        int bucket_pos = shds_hash_bucket_pos(bucket, kvp);

        if(bucket_pos == -1)
        {
            /* hash collision */
            if(bucket->count >= self->bucket_size)
            {
                for(i = 0; i < 5 && bucket->count >= self->bucket_size; ++i)
                {
                    shds_dict_grow(self);
                    pos = shds_hash_index(self, kvp->hash);
                    bucket = self->data[pos];
                }
                assert(i < 5);  /* Prevent memory allocation from exploding */
            }

            bucket->data[bucket->count] = kvp;
            ++bucket->count;
            ++self->len;
        }
        else
        {
            /* Don't return the pointer if it's the same as
               one we're setting */
            if(bucket->data[bucket_pos]->value != kvp->value)
            {
                result = bucket->data[bucket_pos];
            }

            bucket->data[bucket_pos] = kvp;
        }
    }
    else
    {
        bucket = shds_hash_bucket_new(self->bucket_size);
        self->data[pos] = bucket;
        bucket->data[0] = kvp;
        bucket->count = 1;
        ++self->len;
    }

    return result;
}

/* The object version of shds_dict_set */
void shds_dict_set_o(struct ShdsDict * self, struct ShdsKvp * kvp)
{
    struct ShdsObject *object = (struct ShdsObject*)kvp->value;
    ++object->ref_count;
    struct ShdsKvp * result = shds_dict_set(self, kvp);

    if(result)
    {
        shds_kvp_free(result, self->dtor);
    }
}


/* Retrieve the value of the specified key in key, in O(1)
 *
 * @self   The instance
 * @key    Instantiate with the key and a NULL value pointer
 *         if searching for a key/value pair, or re-use a kvp
 * @rm_key Delete the key from the dictionary
 * @return NULL if the value is not in the dictionary, else the value */
void *shds_dict_get(struct ShdsDict *self, struct ShdsKvp *key, int rm_key)
{
    size_t pos = shds_hash_index(self, key->hash);
    struct Shdshash_bucket *bucket = self->data[pos];

    if(!bucket)
    {
        return NULL;
    }

    int bucket_pos = shds_hash_bucket_pos(bucket, key);
    void *result = NULL;

    if(bucket_pos == -1)
    {
        return NULL;
    }
    else
    {
        result = bucket->data[bucket_pos]->value;

        if(rm_key) /* shift the higher keys down 1 position in the bucket */
        {
            size_t i;
            --self->len;
            --bucket->count;
            shds_kvp_free(bucket->data[bucket_pos], NULL);

            for(i = bucket_pos; i < bucket->count; ++i)
            {
                bucket->data[i] = bucket->data[i + 1];
            }
        }

        return result;
    }
}

/* Remove and free a key/value pair from the dictionary if present.
 *
 * @self   The instance
 * @key The key to remove from the dictionary */
void shds_dict_pop(struct ShdsDict * self, struct ShdsKvp *key)
{
    void *value = shds_dict_get(self, key, 1);

    if(self->dtor && value)
    {
        self->dtor(value);
    }
}

/* Return a list of struct ShdsKvp* that are pointers to the originals
 *
 * You can modify the original shds_dict* while iterating the list,
 * but you must not free the dictionary while still using this list,
 * or otherwise free the pointer while it is still being referenced here.
 *
 * @self   The instance
 */
struct ShdsList *shds_dict_items(struct ShdsDict *self)
{
    size_t i, i2;
    struct Shdshash_bucket *bucket;
    struct ShdsList *result = shds_list_new(self->len, NULL);

    for(i = 0; i < self->size; ++i)
    {
        bucket = self->data[i];
        if(bucket)
        {
            for(i2 = 0; i2 < bucket->count; ++i2)
            {
                shds_list_append(result, bucket->data[i2]);
            }
        }
    }

    return result;
}

/* Free a key/value pair, checking that it's not a NULL pointer
 *
 * You must take care of freeing the value and the original key
 *
 * @self  The instance
 * @dtor  The function to free the memory of the value */
void shds_kvp_free(struct ShdsKvp * self, shds_dtor dtor)
{
    if(self)
    {
        if(dtor)
        {
            dtor(self->value);
        }
        shds_free(self->key);
        shds_free(self);
    }
}

/* Free a dictionary
 *
 * @self   The instance
 */
void shds_dict_free(struct ShdsDict * self)
{
    size_t i, i2;
    struct Shdshash_bucket *bucket;

    for(i = 0; i < self->size; ++i)
    {
        bucket = self->data[i];

        if(bucket)
        {
            for(i2 = 0; i2 < bucket->count; ++i2)
            {
                shds_kvp_free(bucket->data[i2], self->dtor);
            }

            shds_hash_bucket_free(bucket);
        }
    }

    shds_free(self->data);
    shds_free(self);
}

/* Queue data structure node */
struct ShdsQueue_node {
    /* A pointer to the next item in the queue */
    struct ShdsQueue_node * next;
    /* A pointer to the data for this item */
    void * data;
};

/* Queue data structure, implemented as a singly-linked-list
 *
 * To avoid potential cross-platform pitfalls and performance
 * problems from defaulting to Spinlock/Mutex/Semaphore, this is
 * BYOC (bring your own concurrency) */
struct ShdsQueue {
    size_t len;
    struct ShdsQueue_node *first;  /* The first item in the queue */
    struct ShdsQueue_node *last; /* The last item in the queue */
    shds_dtor dtor; /* The function to call for freeing queue items */
};

/* The constructor for a queue
 *
 * @dtor  The function to free any objects left in the queue
 *        when the queue is free'd */
struct ShdsQueue *shds_queue_new(shds_dtor dtor)
{
    struct ShdsQueue *result =
        (struct ShdsQueue*)shds_alloc(sizeof(struct ShdsQueue));
    result->len = 0;
    result->first = NULL;
    result->last = NULL;
    result->dtor = dtor;
    return result;
}

/* Append an object to the queue in O(1)
 *
 * @self   The instance
 * @value  A pointer to the value for this queue item */
void shds_queue_push(struct ShdsQueue * self, void *value)
{
    struct ShdsQueue_node * node =
        (struct ShdsQueue_node*)shds_alloc(sizeof(struct ShdsQueue_node));

    node->data = value;

    if(self->last)
    {
        self->last->next = node;
    }
    else
    {
        self->first = node;
    }

    node->next = NULL;
    self->last = node;
    ++self->len;
}

/* The object version of shds_queue_push
 *
 * @self   The instance
 * @object A pointer to a struct ShdsObject */
void shds_queue_push_o(struct ShdsQueue * self, struct ShdsObject *object)
{
    ++object->ref_count;
    shds_queue_push(self, object);
}

/* Retrieve the next object from the queue in O(1)
 *
 * @self   The instance */
void * shds_queue_pop(struct ShdsQueue * self)
{
    if(!self->first)
    {
        return (void*)NULL;
    }

    struct ShdsQueue_node * to_free = self->first;
    void * result = to_free->data;
    self->first = to_free->next;

    shds_free(to_free);
    --self->len;

    return result;
}

/* Empty a queue and free all memory associated with it
 *
 * @self   The instance
 */
void shds_queue_free(struct ShdsQueue *self)
{
    void * data;

    while(1)
    {
        data = shds_queue_pop(self);
        if(!data)
        {
            break;
        }

        if(self->dtor)
        {
            self->dtor(data);
        }
    }

    shds_free(self);
}

/* A byte string */
struct ShdsStr {
    /* The string data */
    char * data;
    /* The length of the string */
    size_t len;
    /* The size of ->data */
    size_t max_size;
};

/* Constructor for a new string from an existing string
 *
 * @data The existing string
 * @len  The length of the string (use strlen()) */
struct ShdsStr *shds_str_new(char * data, size_t len)
{
    struct ShdsStr * result =
        (struct ShdsStr*)shds_alloc(sizeof(struct ShdsStr));
    result->data = data;
    result->len = len;
    result->max_size = len;
    return result;
}

void shds_str_free(void*);
void shds_str_free_a(void*);

/* Constructor for a new, empty string
 *
 * @default_size The amount of string buffer to allocate */
struct ShdsStr *shds_str_empty(size_t default_size)
{
    struct ShdsStr * result =
        (struct ShdsStr*)shds_alloc(sizeof(struct ShdsStr));
    result->data = (char*)shds_alloc(sizeof(char) * default_size);
    result->len = 0;
    result->data[0] = '\0';
    result->max_size = default_size;
    return result;
}

/* Grow a string's char* buffer by doubling it's size.
 *
 * This is called automatically, you should not have to
 * call this manually
 *
 * @self     The instance
 * @max_size The new maximum length */
void shds_str_grow(struct ShdsStr * self, size_t max_size)
{
    self->data = (char*)shds_realloc(self->data, sizeof(char) * max_size);
    self->max_size = max_size;
}

/* Append an existing string to the current string
 *
 * @self   The instance
 * @other  The string to append to the end of @self */
void shds_str_append(struct ShdsStr * self, struct ShdsStr * other)
{
    size_t new_len = self->len + other->len;
    if(new_len >= self->max_size)
    {
        shds_str_grow(self, new_len * 2);
    }

    memcpy(&self->data[self->len], other->data, sizeof(char) * other->len);
    self->len = new_len;
    self->data[self->len] = '\0';
}

/* Create a full copy of an existing string
 *
 * @self   The instance */
struct ShdsStr *shds_str_copy(struct ShdsStr *self)
{
    struct ShdsStr *result = shds_str_empty(self->max_size);
    shds_str_append(result, self);
    return result;
}

/* Create a new string that is a slice of an existing string.
 *
 * Like in Python, the start/end indices can be negative numbers
 *
 * @self      The instance
 * @start     The start index
 * @end       The end index
 * @step_size 1 to copy each item from start to end,
 *            2 to copy every other item, etc... */
struct ShdsStr *shds_str_slice(struct ShdsStr * self,
    int64_t start, int64_t end, int64_t step_size)
{
    size_t i = 0;
    size_t i2;
    struct _shds_slice slice = shds_slice(start, end, step_size, self->len);
    struct ShdsStr *result = shds_str_empty(slice.len + 1);

    if(step_size > 0)
    {
        for(i2 = slice.start; i2 < slice.end; i2 += step_size)
        {
            result->data[i] = self->data[i2];
            ++i;
        }
    }
    else
    {
        for(i2 = slice.end; i2 >= slice.start; i2 += step_size)
        {
            result->data[i] = self->data[i2];
            ++i;
        }
    }

    result->data[slice.len] = '\0';
    result->len = slice.len;
    return result;
}

/* Split a delimited string into a list
 *
 * @self      The instance
 * @delimiter The char to split the string with */
struct ShdsList *shds_str_split(struct ShdsStr * self, char delimiter)
{
    size_t i;
    size_t start = 0;
    struct ShdsList * result = shds_list_new(20, shds_str_free_a);
    struct ShdsStr * str = shds_str_new(NULL, 0);

    for(i = 0; i < self->len; ++i)
    {
        if(self->data[i] == delimiter)
        {
            str->len = (i - start) + 1;
            str->data = (char*)shds_alloc(sizeof(char) * str->len);
            memcpy(str->data, &self->data[start], sizeof(char) * str->len);
            shds_list_append(result, (void*)str);
            start = i + 1;
            str = shds_str_new(NULL, 0);
        }
    }

    str->len = (self->len - start) + 1;
    str->data = (char*)shds_alloc(sizeof(char) * str->len);
    memcpy(str->data, &self->data[start], sizeof(char) * str->len);
    shds_list_append(result, (void*)str);

    return result;
}

/* Join a list of strings into a new string
 *
 * @join_char A char* string to join the elements of @list on
 * @list      The list of strings to join */
struct ShdsStr *shds_str_join(char * join_char, struct ShdsList * list)
{
    struct ShdsStr *result = shds_str_empty(100);
    if(!list->len)
    {
        return result;
    }

    size_t i;
    struct ShdsStr *join_str = NULL;

    if(list->data[0])
    {
        shds_str_append(result, (struct ShdsStr*)list->data[0]);
    }

    if(join_char)
    {
        join_str = shds_str_new(join_char, strlen(join_char));
    }

    for(i = 1; i < list->len; ++i)
    {
        if(join_str)
        {
            shds_str_append(result, join_str);
        }

        if(list->data[i])
        {
            shds_str_append(result, (struct ShdsStr*)list->data[i]);
        }
    }

    if(join_str)
    {
        shds_str_free(join_str);
    }
    return result;
}

/* Generic string matching algorithm to be used by other functions
 *
 * This does not check for NULL termination, you should compare lengths
 * before calling this
 *
 * @self  The string to search
 * @other The string to look for in @self
 * @len   The length of the search*/
int _shds_str_match(char *self, char *other, size_t len)
{
    size_t i;
    size_t last = len - 1;

    /* Typically there's greater probability that *other
     * and *self diverged by their ends, so check those first */
    if(self[0] != other[0] || self[last] != other[last])
    {
        return 0;
    }

    /* Then do a full comparison  */
    for(i = 1; i < last; ++i)
    {
        if(self[i] != other[i])
            return 0;
    }

    return 1;
}

/* Find the next instance of a char in a char*
 *
 * @self   A string
 * @start  The start index to begin searching
 * @length The length of the string
 * @match  The char to search for
 * @escape 0 to ignore chars preceded by a backslash, otherwise 1
 * @return The index of the char, or -1 if not found */
int64_t _shds_str_next_char(char *self, size_t start, size_t length,
    char match, int escape)
{
    size_t i;

    for(i = start; i < length; ++i)
    {
        if(escape && self[i] == '\\')
        {
            ++i;  /* Next char is escaped */
            continue;
        }

        if(self[i] == match)
            return i;
    }

    return  -1;
}

/* Check for the presence of a substring in another string
 *
 * @self  The string to search
 * @other The string to look for in @self
 */
int shds_str_in(struct ShdsStr *self, struct ShdsStr *other)
{
    size_t i;
    size_t len = self->len - other->len + 1;

    for(i = 0; i < len; ++i)
    {
        if(_shds_str_match(&self->data[i], other->data, other->len))
            return 1;
    }

    return 0;
}

/* Check that one string starts with another
 *
 * @self The string to check if starts with @other
 * @other The string to test if @self starts with */
int shds_str_startswith(struct ShdsStr *self, struct ShdsStr *other)
{
    if(other->len > self->len)
    {
        return 0;
    }

    return(_shds_str_match(self->data, other->data, other->len));
}

/* Check that one string ends with another
 *
 * @self The string to check if ends with @other
 * @other The string to test if @self ends with */
int shds_str_endswith(struct ShdsStr *self, struct ShdsStr *other)
{
    if(other->len > self->len)
    {
        return 0;
    }

    size_t end_index = self->len - other->len;

    return(_shds_str_match(&self->data[end_index], other->data, other->len));
}

/* Generate a list from a string where each pointer in the list points
 * to a char in the string
 *
 * This is useful for doing things like sorting the chars, etc...
 *
 * @self   The instance
 * @return A list containing pointers to each char */
struct ShdsList *shds_str_to_list(struct ShdsStr *self)
{
    size_t i;
    struct ShdsList *result = shds_list_new(self->len, NULL);

    for(i = 0; i < self->len; ++i)
    {
        shds_list_append(result, &self->data[i]);
    }

    return result;
}

/* Convert a list of char* to a string, use with shds_str_to_list().
 *
 * The char* must point to a single char, not a dynamic array
 *
 * @self   The instance
 * @return A string containing the dereferenced chars in @self */
struct ShdsStr *shds_list_to_str(struct ShdsList *self)
{
    size_t i;
    struct ShdsStr *result = shds_str_empty(self->len + 1);

    for(i = 0; i < self->len; ++i)
    {
        result->data[i] = *(char*)self->data[i];
    }

    result->data[i] = '\0';
    return result;
}

/* Free the data structure, but NOT the underlying string
 *
 * @self A pointer to a struct ShdsStr */
void shds_str_free(void *self)
{
    shds_free(self);
}

/* Free the data structure AND it's underlying string
 *
 * @self A pointer to a struct ShdsStr */
void shds_str_free_a(void *str)
{
    struct ShdsStr *self = (struct ShdsStr*)str;
    shds_free(self->data);
    shds_free(self);
}

#endif /*LIBSHDS_H*/

