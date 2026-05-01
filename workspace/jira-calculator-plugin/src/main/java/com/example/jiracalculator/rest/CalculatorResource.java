package com.example.jiracalculator.rest;

import javax.ws.rs.Consumes;
import javax.ws.rs.POST;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;

@Path("/calculate")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class CalculatorResource {

    @POST
    public Response calculate(CalculateRequest request) {
        if (request == null
                || request.getOperand1() == null
                || request.getOperand2() == null
                || request.getOperator() == null) {
            return Response.status(400)
                    .entity("{\"error\":\"operand1, operand2, operator are required\"}")
                    .build();
        }

        double operand1;
        double operand2;
        try {
            operand1 = Double.parseDouble(request.getOperand1());
            operand2 = Double.parseDouble(request.getOperand2());
        } catch (NumberFormatException e) {
            return Response.status(400)
                    .entity("{\"error\":\"Invalid number format\"}")
                    .build();
        }

        String operator = request.getOperator().trim();
        double result;

        switch (operator) {
            case "+":
                result = operand1 + operand2;
                break;
            case "-":
                result = operand1 - operand2;
                break;
            case "*":
                result = operand1 * operand2;
                break;
            case "/":
                if (operand2 == 0) {
                    return Response.status(400)
                            .entity("{\"error\":\"Division by zero\"}")
                            .build();
                }
                result = operand1 / operand2;
                if (Double.isInfinite(result) || Double.isNaN(result)) {
                    return Response.status(400)
                            .entity("{\"error\":\"Division by zero\"}")
                            .build();
                }
                break;
            default:
                return Response.status(400)
                        .entity("{\"error\":\"Unsupported operator: " + operator + "\"}")
                        .build();
        }

        String expression = request.getOperand1() + " " + operator + " " + request.getOperand2() + " = " + formatResult(result);
        String json = "{\"result\":" + result + ",\"expression\":\"" + expression + "\"}";
        return Response.ok(json).build();
    }

    private String formatResult(double value) {
        if (value == Math.floor(value) && !Double.isInfinite(value)) {
            return String.valueOf((long) value);
        }
        return String.valueOf(value);
    }

    public static class CalculateRequest {
        private String operand1;
        private String operator;
        private String operand2;

        public String getOperand1() { return operand1; }
        public void setOperand1(String operand1) { this.operand1 = operand1; }

        public String getOperator() { return operator; }
        public void setOperator(String operator) { this.operator = operator; }

        public String getOperand2() { return operand2; }
        public void setOperand2(String operand2) { this.operand2 = operand2; }
    }
}
