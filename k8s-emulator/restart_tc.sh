current_epoch=$(date +%s)

# Round up or round down, and add 2 minutes delay
target_epoch=$(date -d @$(( (($(date +%s) + 30) / 60) * 60 + 120)) +%s)
# date -d @$(( (($(date +%s) + 150) / 300) * 300)) "+%Y_%m_%d_%H_%M"

echo "Current epoch: ${current_epoch}"
echo "Target epoch:  ${target_epoch}"

current_dir=$(pwd)
# echo ${current_dir}
# VM_ARRAY=$(vagrant global-status | awk -v current_dir="$current_dir" '$5 == current_dir {print $1}')
VM_ARRAY=$(vagrant global-status | awk -v current_dir="$current_dir" '{if ($4=="running" && $5==current_dir) {print $1}}')
for i in ${VM_ARRAY[@]}
do
    (vagrant ssh $i -c "sh /vagrant/utils/restart_tc_at_time.sh ${target_epoch}" &)
    echo "Command completed for (by placing in background): $i"
done 
target_epoch_readable=$(date -d @${target_epoch})
echo "Check back at $target_epoch_readable"

# Sleep for remaining time:
current_epoch=$(date +%s)
sleep_seconds=$(( $target_epoch - $current_epoch ))
sleep $sleep_seconds
