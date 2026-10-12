#1 第一题
s=0
for i in range(2,101,2):
    s=s+i
print(s)



#2 第二题
s=0
for i in range (1,10,1):
    s=s+i*(i+1)
print(s)


#3 第三题
s=0
for i in range(1,10):
    s=s+1/i/(i+1)
print(s)

 
#4 第四题
n=int(input())
pai=0
for i in range (0,n):
    if i%2==0:
        pai=pai+1/(2*i+1)
    else:
        pai=pai-1/(2*i+1)
print(4*pai)
        
