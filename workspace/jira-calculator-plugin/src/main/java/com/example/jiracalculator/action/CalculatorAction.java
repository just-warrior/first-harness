package com.example.jiracalculator.action;

import com.atlassian.jira.web.action.JiraWebActionSupport;
import com.atlassian.jira.security.request.SupportedMethods;
import com.atlassian.jira.security.request.RequestMethod;

@SupportedMethods({RequestMethod.GET, RequestMethod.POST})
public class CalculatorAction extends JiraWebActionSupport {

    @Override
    public String doDefault() throws Exception {
        return INPUT;
    }

    @Override
    public String execute() throws Exception {
        return INPUT;
    }
}
