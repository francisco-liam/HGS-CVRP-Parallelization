cd build || exit

for i in {1..10}; do
    ./hgs ../Instances/ECVRP/X-n147-k7-s4.evrp "147-1-$i.sol" -seed "$i" -t 340.8
    sleep 1
done

for i in {1..10}; do
    ./hgs ../Instances/ECVRP/X-n221-k11-s7.evrp "221-1-$i.sol" -seed "$i" -t 511.2
    sleep 1
done

for i in {1..10}; do
    ./hgs ../Instances/ECVRP/X-n360-k40-s9.evrp "360-1-$i.sol" -seed "$i" -t 840
    sleep 1
done

for i in {1..10}; do
    ./hgs ../Instances/ECVRP/X-n469-k26-s10.evrp "469-1-$i.sol" -seed "$i" -t 1099.2
    sleep 1
done

for i in {1..10}; do
    ./hgs ../Instances/ECVRP/X-n577-k30-s4.evrp "577-1-$i.sol" -seed "$i" -t 1372.8
    sleep 1
done

for i in {1..10}; do
    ./hgs ../Instances/ECVRP/X-n698-k75-s13.evrp "698-1-$i.sol" -seed "$i" -t 1641.6
    sleep 1
done

for i in {1..10}; do
    ./hgs ../Instances/ECVRP/X-n759-k98-s10.evrp "759-1-$i.sol" -seed "$i" -t 1795.2
    sleep 1
done

for i in {1..10}; do
    ./hgs ../Instances/ECVRP/X-n830-k171-s11.evrp "830-1-$i.sol" -seed "$i" -t 1963.2
    sleep 1
done

for i in {1..10}; do
    ./hgs ../Instances/ECVRP/X-n920-k207-s4.evrp "920-1-$i.sol" -seed "$i" -t 2196
    sleep 1
done

for i in {1..10}; do
    ./hgs ../Instances/ECVRP/X-n1006-k43-s5.evrp "1006-1-$i.sol" -seed "$i" -t 2400
    sleep 1
done
