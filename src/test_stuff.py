'''
Created on Jul 21, 2010

@author: dannygoodman
'''

x='0b01010'
print x.split('b')


a = {1:1,2:2,3:3}
for k,v in a.items():
    print k, v
    
b = 5 if True else 4
name = {}
if name:
    print 'True'
else:
    print 'false'
print 'done'