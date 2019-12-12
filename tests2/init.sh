# supplmentatry functions for python test

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

function show_usage ()
{
        echo "Usage: $0 [OPTIONS]"
        echo " OPTIONS"
        echo " -p arg   Set python binary to use"
        echo " -m       Run with MemoryLeak Test (valgrind is required)"
        echo " -a       Run all TestCases including performance test"
}

function get_options ()
{
  while getopts "amp:" opt; do
    case $opt in
      m ) test_mode="with_MemoryLeak" ;;
      p ) python="$OPTARG" ;;
      a ) test_case="all TestCases (functional, performance)" ;;
      h|\?|* ) show_usage; exit 1;;
    esac
  done
}
