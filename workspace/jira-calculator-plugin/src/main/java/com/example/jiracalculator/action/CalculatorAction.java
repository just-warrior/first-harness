package com.example.jiracalculator.action;

import com.atlassian.jira.security.request.RequestMethod;
import com.atlassian.jira.security.request.SupportedMethods;
import com.atlassian.jira.web.action.JiraWebActionSupport;

// @Component 금지 — PITFALL-08: ConfigurationClassParser가 I18nHelper를 OSGi 경계 너머로 스캔하여 BeanDefinitionStoreException 발생
// plugin-context.xml의 <bean> 선언으로 직접 등록
@SupportedMethods({RequestMethod.GET, RequestMethod.POST})
public class CalculatorAction extends JiraWebActionSupport {

    // GET 진입점 — calculator.vm 렌더링 (PITFALL-01: !default.jspa suffix로 호출)
    @Override
    public String doDefault() throws Exception {
        return INPUT;
    }

    // POST 폼 제출 처리 — 계산은 REST API에서 수행하므로 파라미터 null guard 후 뷰 반환
    @Override
    protected String doExecute() throws Exception {
        return INPUT;
    }
}
