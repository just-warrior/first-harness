package com.example.jiracalculator.action;

import com.atlassian.jira.web.action.JiraWebActionSupport;
import com.atlassian.jira.security.request.RequestMethod;
import com.atlassian.jira.security.request.SupportedMethods;

// Skill 7: WebWork Action에는 @Named 사용 금지 — Jira 프레임워크가 직접 인스턴스화
@SupportedMethods({RequestMethod.GET, RequestMethod.POST})
public class CalculatorAction extends JiraWebActionSupport {

    @Override
    public String doDefault() throws Exception {
        return INPUT;
    }

    @Override
    protected String doExecute() throws Exception {
        return SUCCESS;
    }
}
