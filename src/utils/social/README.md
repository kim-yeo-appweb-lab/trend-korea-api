# social

소셜 로그인 Provider를 공통 인터페이스로 다루기 위한 베이스 모듈입니다.

## 주요 파일
- `base.py`: `SocialAuthProvider` 추상 클래스, `SocialUser` 데이터 모델
- `registry.py`: Provider 등록/조회 레지스트리

## 사용 목적
- Provider별 구현체(예: kakao/naver/google)를 동일 인터페이스로 연결
- 인증 라우터에서 provider 이름으로 구현체를 찾아 사용

## 구현 패턴
1. `SocialAuthProvider`를 상속한 provider 클래스 구현
2. `provider_name` 지정
3. `exchange_code()` 구현
4. 앱 초기화 시 `SocialProviderRegistry.register()` 호출
