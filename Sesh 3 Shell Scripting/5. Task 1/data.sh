date # Can also do, curDate=$(date) and use it as echo $curDate
hostname
uname
ps > process.log

echo $'\n'
cat process.log

echo $'\n'

read -p "Enter your name: " name
read -p "Enter your roll number: " roleno
read -p "Enter your comment: " comment

echo $'\n'

echo "Your name is $name, roll number is $roleno and comment is $comment"

# Using echo $'\n' like $'' makes the \n interpretable