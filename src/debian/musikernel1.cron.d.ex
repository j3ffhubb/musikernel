#
# Regular cron jobs for the musikernel2 package
#
0 4	* * *	root	[ -x /usr/bin/musikernel2_maintenance ] && /usr/bin/musikernel2_maintenance
