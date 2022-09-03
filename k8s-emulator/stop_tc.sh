# NOTE: this is currently just a brute force approach. Not automated yet. Just a convenience script for now. Because I do not automate finding the interface to del qdisc, instead I just assume I know the interfaces to remove. 

current_epoch=$(date +%s)

# Round up or round down, and add 1 minutes delay
target_epoch=$(date -d @$(( (($(date +%s) + 30) / 60) * 60 + 60)) +%s)
# date -d @$(( (($(date +%s) + 150) / 300) * 300)) "+%Y_%m_%d_%H_%M"

echo "Current epoch: ${current_epoch}"
echo "Target epoch:  ${target_epoch}"

current_dir=$(pwd)
# echo ${current_dir}
# VM_ARRAY=$(vagrant global-status | awk -v current_dir="$current_dir" '$5 == current_dir {print $1}')
VM_ARRAY=$(vagrant global-status | awk -v current_dir="$current_dir" '{if ($4=="running" && $5==current_dir) {print $1}}')
for i in ${VM_ARRAY[@]}
do
    (vagrant ssh $i -c "sudo systemctl disable --now tc_mod.timer; sudo systemctl stop --now tc_mod.timer; sudo tc qdisc del dev eth1 root; sudo tc qdisc del dev eth4 root; sudo tc qdisc del dev eth2 root; sudo tc qdisc del dev eth3 root;" &)
    echo "Command completed for (by placing in background): $i"
done 
target_epoch_readable=$(date -d @${target_epoch})
echo "Check back at $target_epoch_readable"

# Sleep for remaining time:
current_epoch=$(date +%s)
sleep_seconds=$(( $target_epoch - $current_epoch ))
sleep $sleep_seconds