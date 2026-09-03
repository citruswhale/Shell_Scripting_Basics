# sum of 1 to n
read -p "Enter a number: " n
sum=0
for ((i=1; i<=n; i++)); do # can do spread operator sorta stuff like for i in {1..5} for finite ranges
  ((sum+=i)) # can also do sum=$((sum+i))
done
echo "Sum is $sum"