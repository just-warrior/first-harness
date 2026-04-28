package com.example.jiracalculator.rest;

import javax.ws.rs.Consumes;
import javax.ws.rs.POST;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;
import com.example.jiracalculator.service.CalculatorService;
import javax.inject.Inject;

@Path("/calculate")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class CalculatorResource {

    private final CalculatorService calculatorService;

    @Inject
    public CalculatorResource(CalculatorService calculatorService) {
        this.calculatorService = calculatorService;
    }

    @POST
    public Response calculate(CalculationRequest request) {
        if (request == null) {
            return errorResponse("Invalid input. Please enter valid numbers.");
        }

        double num1;
        double num2;
        try {
            num1 = parseNumber(request.getNum1());
            num2 = parseNumber(request.getNum2());
        } catch (NumberFormatException e) {
            return errorResponse("Invalid input. Please enter valid numbers.");
        }

        String operator = request.getOperator();
        if (operator == null || operator.isEmpty()) {
            return errorResponse("Invalid input. Please enter valid numbers.");
        }

        double result;
        try {
            result = calculatorService.calculate(num1, num2, operator);
        } catch (ArithmeticException e) {
            return errorResponse("Cannot divide by zero.");
        } catch (IllegalArgumentException e) {
            return errorResponse(e.getMessage());
        }

        String resultJson = "{\"result\":" + calculatorService.formatResult(result) + "}";
        return Response.ok(resultJson).build();
    }

    private double parseNumber(String value) {
        if (value == null || value.trim().isEmpty()) {
            throw new NumberFormatException("Number is null or empty");
        }
        return Double.parseDouble(value.trim());
    }

    private Response errorResponse(String message) {
        String json = "{\"error\":\"" + message.replace("\"", "\\\"") + "\"}";
        return Response.status(Response.Status.BAD_REQUEST).entity(json).build();
    }

    public static class CalculationRequest {
        private String num1;
        private String num2;
        private String operator;

        public String getNum1() { return num1; }
        public void setNum1(String num1) { this.num1 = num1; }

        public String getNum2() { return num2; }
        public void setNum2(String num2) { this.num2 = num2; }

        public String getOperator() { return operator; }
        public void setOperator(String operator) { this.operator = operator; }
    }
}
