if [ "$#" != "1" ]; then
  echo "Usage: sh restart_tc_at_time.sh [seconds_since_epoch]"
  exit 0
fi

current_epoch=$(date +%s)
target_epoch=$1

sleep_seconds=$(( $target_epoch - $current_epoch ))

sleep $sleep_seconds

sed -i '1s/.*/'1'/' /tmp/temp_tc_count_store.txt