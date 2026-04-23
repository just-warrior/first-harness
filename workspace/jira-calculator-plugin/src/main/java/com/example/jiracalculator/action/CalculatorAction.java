package com.example.jiracalculator.action;

import com.atlassian.jira.web.action.JiraWebActionSupport;
import com.atlassian.jira.security.request.RequestMethod;
import com.atlassian.jira.security.request.SupportedMethods;

import java.util.ArrayList;
import java.util.List;

@SupportedMethods({RequestMethod.GET, RequestMethod.POST})
public class CalculatorAction extends JiraWebActionSupport {

    private String expression;
    private String result;
    private List<String> history = new ArrayList<>();

    @Override
    public String doDefault() throws Exception {
        return INPUT;
    }

    @Override
    protected String doExecute() throws Exception {
        if (expression == null || expression.trim().isEmpty()) {
            return SUCCESS;
        }
        return SUCCESS;
    }

    public String getExpression() { return expression; }
    public void setExpression(String expression) { this.expression = expression; }

    public String getResult() { return result; }
    public void setResult(String result) { this.result = result; }

    public List<String> getHistory() { return history; }
    public void setHistory(List<String> history) { this.history = history; }
}
