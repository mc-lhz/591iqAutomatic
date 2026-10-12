#1 第一题
s=0
for i in range(2,101,2):
    s=s+i
print(s)

#2 第二题
s=0
for i in range(1,10):
    s=s+i*(i+1)
print(s)

#3 第三题
s=0
for i in range(2,11):
    s=s+1/(i*(i-1))
print(s)

 
#4 第四题
s=0
n=int(input())
for i in range(1,n+1,4):
    s=s+4*(1/i-1/(i+2))
print(s)
