package com.example.jiracalculator.rest;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import javax.ws.rs.Consumes;
import javax.ws.rs.POST;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;

// DI 어노테이션(@Named 등) 금지 — <rest> 모듈 디스크립터가 패키지 스캔으로 직접 등록 (PITFALL-03)
// JAX-RS 어노테이션은 javax.ws.rs.* 사용 — jakarta.ws.rs.* 절대 금지 (PITFALL-03, Skill 8)
@Path("/calculate")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class CalculatorResource {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    @POST
    public Response calculate(String requestBody) {
        try {
            JsonNode request = MAPPER.readTree(requestBody);
            String operand1Str = request.path("operand1").asText();
            String operator = request.path("operator").asText();
            String operand2Str = request.path("operand2").asText();

            double operand1 = Double.parseDouble(operand1Str);
            double operand2 = Double.parseDouble(operand2Str);

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
                        return errorResponse("0으로 나눌 수 없습니다.");
                    }
                    result = operand1 / operand2;
                    break;
                default:
                    return errorResponse("지원하지 않는 연산자입니다: " + operator);
            }

            String resultStr = (result == Math.floor(result) && !Double.isInfinite(result))
                    ? String.valueOf((long) result)
                    : String.valueOf(result);

            String expression = operand1Str + " " + operator + " " + operand2Str + " = " + resultStr;

            ObjectNode response = MAPPER.createObjectNode();
            response.put("result", result);
            response.put("expression", expression);
            return Response.ok(MAPPER.writeValueAsString(response)).build();

        } catch (NumberFormatException e) {
            return errorResponse("유효하지 않은 숫자 형식입니다.");
        } catch (Exception e) {
            return errorResponse("계산 중 오류가 발생했습니다: " + e.getMessage());
        }
    }

    private Response errorResponse(String message) {
        try {
            ObjectNode error = MAPPER.createObjectNode();
            error.put("error", message);
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(MAPPER.writeValueAsString(error))
                    .build();
        } catch (Exception e) {
            return Response.serverError().entity("{\"error\":\"Internal error\"}").build();
        }
    }
}
