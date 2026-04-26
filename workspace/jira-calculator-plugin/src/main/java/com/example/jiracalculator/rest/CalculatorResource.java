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
    public Response calculate(CalculationRequest request) {
        if (request == null) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(new CalculationResponse(null, "Error: Invalid input"))
                    .build();
        }

        try {
            double operand1 = parseOperand(request.getOperand1());
            double operand2 = parseOperand(request.getOperand2());
            double result = compute(operand1, request.getOperator(), operand2);
            return Response.ok(new CalculationResponse(formatResult(result), null)).build();
        } catch (ArithmeticException e) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(new CalculationResponse(null, "Error: Division by zero"))
                    .build();
        } catch (NumberFormatException e) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(new CalculationResponse(null, "Error: Invalid number format"))
                    .build();
        } catch (UnsupportedOperationException e) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(new CalculationResponse(null, e.getMessage()))
                    .build();
        }
    }

    private double parseOperand(String value) {
        if (value == null || value.trim().isEmpty()) {
            throw new NumberFormatException("Operand is null or empty");
        }
        return Double.parseDouble(value.trim());
    }

    private double compute(double a, String operator, double b) {
        if (operator == null) {
            throw new UnsupportedOperationException("Error: Operator is required");
        }
        switch (operator.trim()) {
            case "+": return a + b;
            case "-": return a - b;
            case "*": return a * b;
            case "/":
                if (b == 0) throw new ArithmeticException("Division by zero");
                return a / b;
            default:
                throw new UnsupportedOperationException("Error: Unsupported operator '" + operator + "'");
        }
    }

    private String formatResult(double value) {
        if (value == Math.floor(value) && !Double.isInfinite(value)) {
            return String.valueOf((long) value);
        }
        return String.valueOf(value);
    }

    public static class CalculationRequest {
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

    public static class CalculationResponse {
        private String result;
        private String error;

        public CalculationResponse(String result, String error) {
            this.result = result;
            this.error = error;
        }

        public String getResult() { return result; }
        public String getError() { return error; }
    }
}
