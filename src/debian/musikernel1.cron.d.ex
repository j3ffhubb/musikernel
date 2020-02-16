#
# Regular cron jobs for the musikernel3 package
#
0 4	* * *	root	[ -x /usr/bin/musikernel3_maintenance ] && /usr/bin/musikernel3_maintenance
