# 패키지를 선언하는 파일
# 애니몰 패키지가 어떤 파일들의 합인지 소개

from .cat import Cat # . <-- "이 폴더에 있는" cat.py 이라는 파일에서 Cat 라는 클래스를 가지고 와
from .dog import Dog # . <-- "현재 폴더에 있는" dog.py 이라는 파일에서 Dog 라는 클래스를 가지고 와