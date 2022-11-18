__FRAME__ = 0x800000

def zip(sender, receiver, request=0, state=0, control=0) -> int:
    '''
    프로토콜 코드를 압축해서 int값으로 리턴하는 함수
      Args
        sender: 요청자 코드         (2bit)
        receiver: 수신자 코드       (2bit)
        request: 요청 코드          (8bit)
        state: 응답 상태            (3bit)
        control: 제어 코드          (8bit)
      
      Return
        int형 압축된 코드
      
      Example
        센서파이가 PC에 요청하는 ping 보내기
          센서파이 -> PC: zip(2, 1)
          PC -> 센서파이: zip(1, 2)

        센서파이의 인식결과 요청에 대해 PC가 보내는 마스크 인식 결과 전송
          센서파이 -> PC: zip(2, 1, 4, 1)
          PC -> 센서파이: zip(1, 2, 4, 2)
          PC -> 센서파이: zip(1, 2, 4, 3)
          센서파이 -> PC: zip(2, 1, 4, 2)\n
          pc가 0 또는 1을 보냄
          PC -> 센서파이: zip(1, 2, 4, 4)\n
          통신 종료
    '''
    return __FRAME__ | (sender << 21) | (receiver << 19) | (request << 11) | (state << 8) | control

def unzip(zipped_code):
    sender = (zipped_code & 0x600000) >> 21
    receiver = (zipped_code & 0x180000) >> 19
    request = (zipped_code & 0x7F800) >> 11
    state = (zipped_code & 0x700) >> 8
    control = (zipped_code & 0xFF)

    unzipped_dict = {
        'sender': sender,
        'receiver': receiver,
        'request': request,
        'state': state,
        'control': control
    }

    return unzipped_dict
