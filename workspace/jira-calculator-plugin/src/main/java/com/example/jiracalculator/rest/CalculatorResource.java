package com.example.jiracalculator.rest;

import javax.ws.rs.Consumes;
import javax.ws.rs.POST;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;

// PITFALL-03: javax.ws.rs (not jakarta.ws.rs)
// Skill 2: No @Named annotation on REST resource
@Path("/calculate")
public class CalculatorResource {

    @POST
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response calculate(CalculationRequest request) {
        if (request == null || request.getOperand1() == null || request.getOperand2() == null || request.getOperator() == null) {
            return Response.ok(new CalculationResponse(null, "Missing required fields")).build();
        }

        try {
            double a = Double.parseDouble(request.getOperand1().trim());
            double b = Double.parseDouble(request.getOperand2().trim());
            double result;

            switch (request.getOperator()) {
                case "+":
                    result = a + b;
                    break;
                case "-":
                    result = a - b;
                    break;
                case "*":
                    result = a * b;
                    break;
                case "/":
                    if (b == 0) {
                        return Response.ok(new CalculationResponse(null, "Cannot divide by zero")).build();
                    }
                    result = a / b;
                    break;
                default:
                    return Response.ok(new CalculationResponse(null, "Invalid operator: " + request.getOperator())).build();
            }

            return Response.ok(new CalculationResponse(result, null)).build();

        } catch (NumberFormatException e) {
            return Response.ok(new CalculationResponse(null, "Invalid number format")).build();
        }
    }

    // Jackson requires default constructor + getter/setter for deserialization
    public static class CalculationRequest {
        private String operand1;
        private String operator;
        private String operand2;

        public CalculationRequest() {}

        public String getOperand1() { return operand1; }
        public void setOperand1(String operand1) { this.operand1 = operand1; }

        public String getOperator() { return operator; }
        public void setOperator(String operator) { this.operator = operator; }

        public String getOperand2() { return operand2; }
        public void setOperand2(String operand2) { this.operand2 = operand2; }
    }

    // Jackson requires default constructor for serialization in some contexts
    public static class CalculationResponse {
        private Double result;
        private String error;

        public CalculationResponse() {}

        public CalculationResponse(Double result, String error) {
            this.result = result;
            this.error = error;
        }

        public Double getResult() { return result; }
        public void setResult(Double result) { this.result = result; }

        public String getError() { return error; }
        public void setError(String error) { this.error = error; }
    }
}
