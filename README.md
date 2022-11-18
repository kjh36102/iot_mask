## 개발 과제
- ~~마스크 인식 AI 준비~~
- ~~TTS녹음 준비~~
- 소켓통신
- ~~초음파센서~~
- 인체감지센서
- ~~체온센서~~
- ~~서보모터~~
- ~~LCD(lcd드라이버 사용)~~
- 음성재생
- 케이스제작
- 프로토콜 정의

---

# 프로토콜
프로토콜은 1:1 통신상황을 가정하여 만듦, 빠르고 정확한 통신을 위해 String 명령어를 이용하는 것보다 4byte(32bit)명령어를 이용하는 것이 통신속도에 있어 이득이므로 4byte 명령어를 사용할 예정

### 기본 형태
`[요청자:4bit][수신자:4bit][요청 코드:1byte][응답상태:1byte][제어코드:1byte]`<br>
- 모든 요청에서, 요청을 받은 쪽은 요청확인을 보내줘야 함
- 모든 응답데이터 보내기에서, 보내기 전 시작을 알리고 끝날때도 알려줘야 함
- 오류나 로그 데이터도 위와 마찬가지임

## 코드
### 요청자 및 수신자
|코드|10진|설명|
|-----|-----|-----|
|0001|1|PC|
|0010|2|센서파이|
|0011|3|AI파이|

### 요청코드
|코드|10진|설명|기대응답|응답형태|
|-----|-----|------|-------|-----|
|0000 0001|1|마스크 인식 사용가능 여부|사용 가능 여부|0 or 1|
|0000 0010|2|인식 시작 요청|시작 성공 여부|0 or 1|
|0000 0011|3|인식 중단 요청|중단 성공 여부|0 or 1|
|0000 0100|4|인식 결과 요청|인식 결과|0 or 1|

### 응답상태
|코드|10진|설명
|-----|---|----|
|0000 0001|1|요청|
|0000 0010|2|요청 확인|
|0000 0011|3|응답 데이터 송신 시작|
|0000 0100|4|응답 데이터 송신 종료|
|0000 0101|5|로그 송신 시작|
|0000 0110|6|로그 송신 종료|
|0000 0111|7|오류 로그 송신 시작|
|0000 1000|8|오류 로그 송신 종료|

#### 통신 시나리오
> 추가예정

---

# 프로젝트 개요
라즈베리파이4를 이용한 건물 입장 시 시행되는 방역관리 조치를 자동화 해주는 IoT 시스템

본 프로젝트에서 만들고자 하는 것은, 건물 출입 시 방역 관리 조치를 자동화하는 제품입니다. 일반적으로 널리 시행되는 조치인 마스크 착용 검사, 발열 측정, 손 소독, 출입관리 등을 자동화하여 불필요하게 인력이 사용되는 것을 막고 궁극적으로 바이러스 감염의 확산을 방지하는 것이 목표입니다.
위의 내용을 토대로 만들고자 하는 제품의 이름을 ‘AI 방역 관리기’라고 이름 지었습니다.

## 개발 동기 및 필요성
현재 COVID-19가 세계적 전염병으로 퍼짐에 따라 공공장소에서 마스크 착용이 의무화된 지 오래입니다. 하지만, 마스크 착용 권장 장기화에 따라 공공장소에서 마스크를 제대로 착용하지 않거나, 아예 쓰지 않는, 이른바 부적절한 착용도 많아지게 되었습니다. 사람이 눈으로 직접 마스크 미착용자를 식별하는 것은 인력이 필요하고, 또 사람이 하는 일이기에 확인하지 못하는 부분이 생길 것입니다. 따라서 공공장소 및 전염 위험이 있는 주요 지역의 입구에서 AI 방역 관리기를 이용하여 마스크 미착용자를 식별, 길을 막아 방역 조치를 받은 후에 통과하게 하여 궁극적으로는 불필요한 인력 사용 감소 및 바이러스 감염 확산을 방지하는 데 도움이 되리라 생각했습니다.

# 예상 완성도
![화면 캡처 2022-11-13 040012](https://user-images.githubusercontent.com/88638058/201494700-30e55120-7574-482d-bb2e-2e4152e57884.png)
![화면 캡처 2022-11-13 040035](https://user-images.githubusercontent.com/88638058/201494731-09ee097b-9735-437b-a59f-e10c441a558c.png)
![화면 캡처 2022-11-13 040141](https://user-images.githubusercontent.com/88638058/201494734-e81519dc-ff2f-4c19-aba9-25c99604414a.png)


---

# 프로젝트 개발
프로젝트 개발은 컴포넌트 기반 개발 기법을 이용해서 필요한 기능과 인터페이스를 디자인하고 조합하기로 했습니다.

## 플로우 차트
![화면 캡처 2022-11-13 035604](https://user-images.githubusercontent.com/88638058/201494684-24d39b6b-4593-4d04-9083-da6ae3384c48.png)


## 사용자 시나리오
사용자들이 일렬로 바리케이드 앞에 줄을 선다. 사용자들이 바리케이드 앞에 서 있는지는 초음파 센서를 이용해서 감지한다. 사람이 서 있다고 판단했기에 ‘카메라를 봐주세요.’라는 안내음성을 재생한다. 안내음성이 끝나고 2초 정도 뒤 카메라로 사진을 찍어 PC에 전송한다. PC는 전송받은 이미지를 AI 모델에 입력으로 넣는다. 모델은 이미지를 분석할 때 여러 사람의 얼굴이 감지되었다면, 가장 얼굴 영역이 넓은 사람의 결과를 라즈베리파이에 돌려준다. 라즈베리파이는 결과를 받아 미착용자라면 ‘마스크를 착용해주세요.’라는 안내음성을 재생한 뒤 위의 과정을 반복한다. 반면 마스크를 잘 착용했다면 ‘체온측정기에 손목을 대주세요.’라는 음성을 재생한다. 체온이 인간의 체온 근처인 36.5도에 근접하지 않는다면 안내음성을 반복 재생한다. 사용자의 손목 체온을 재는 데 성공했다면, 온도를 보고 38도 이상 시 ‘체온이 높아 입장하실 수 없습니다.’라는 안내음성을 재생한다. 체온이 정상 범위라면 ‘손 소독제 사출구에 손을 넣으십시오.’라는 음성을 재생한다. 사출구 내부에서 센서를 이용해 손이 감지되면, 손 소독제를 살포한다. 이 모든 과정이 끝나면 바리케이드가 열린다. 입장한 사람의 사진과 측정값은 DB에 저장되어 추후 관리자가 통곗값을 보기 위해 웹서버에 접속할 수 있다.

---

# 개발자들
### 개발 참여
- 조선대학교 컴퓨터공학과 18학번 김주현
- 조선대학교 컴퓨터공학과 18학번 송민석

### 아이디어 제안
- 송민석
