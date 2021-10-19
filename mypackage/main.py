# animal package
# dog, cat modules
# dog, cat modules can say "hi"

from animal import dog # animal 패키지에서 dog 라는 모듈을 가지고 와
from animal import cat # animal 패키지에서 cat 라는 모듈을 가지고 와

from animal import * 

# from animal.dog import Dog
#      ^애니몰 패키지, dog 파일, Dog 클래스

d = dog.Dog() # instance
d.hi()

d = cat.Cat()
d.hi()

!sys