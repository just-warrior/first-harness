# Fix History

## [FIX-01] MyComponentWiredTest.java 컴파일 오류 (2026-04-23)

**이유:** Chapter 2-2에서 `atlassian-plugins-osgi-testrunner` 의존성을 pom.xml에서 제거했으나, 해당 의존성에 종속된 스캐폴딩 통합 테스트 파일(`MyComponentWiredTest.java`)을 삭제하지 않아 `-DskipTests` 빌드 시 테스트 컴파일 단계에서 `com.atlassian.plugins.osgi.test.AtlassianPluginsTestRunner` 심볼을 찾지 못해 BUILD FAILURE 발생.

**방법:** `src/test/java/it/com/example/jiracalculator/MyComponentWiredTest.java` 삭제. 이 파일은 atlas-create-jira-plugin 스캐폴딩 생성물이며, 프로젝트의 실제 단위 테스트(`CalculatorServiceTest`)와 무관한 OSGi 통합 테스트 보일러플레이트임.

**기대효과:** `atlas-mvn clean package -DskipTests` 빌드가 테스트 컴파일 오류 없이 BUILD SUCCESS로 완료됨.
