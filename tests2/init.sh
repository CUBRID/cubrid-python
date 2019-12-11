# supplmentatry functions for python test


function find_python ()
{
        arg=$(echo $* | cut -d'=' -f1-1)
        if [ x$arg = "xpython" ];then
                arg=$(echo $* | cut -d'=' -f2-2)
                echo $arg
        else
                echo "python"   # Use default
        fi
}

function check_verdict ()
{
	if [ ! -f $1 ];then
		echo "NONE"
		return
	fi

	verdict=$(grep FAILED $1)
	if [ -z "$verdict" ];then
		verdict="Passed"
	else
		verdict=$(echo $verdict | cut -d ':' -f2-2);
	fi
	echo $verdict
}

function python_version_check ()
{
	local version=$($1 --version 2>&1)
	local major=$(echo $version | cut -d ' ' -f2-2)
	major=${major:0:1}

	echo $major
}
