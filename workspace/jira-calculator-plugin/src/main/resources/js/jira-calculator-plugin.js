AJS.$(function ($) {
    'use strict';

    var expression = '';
    var justCalculated = false;
    var history = [];

    // ── Helpers ─────────────────────────────────────────────────────────────

    function isOperator(ch) {
        return ch === '+' || ch === '-' || ch === '*' || ch === '/';
    }

    function updateDisplay(val) {
        var $d = $('#calc-expression');
        $d.val(val);
        $d.attr('placeholder', val === '' ? '0' : '');
    }

    function formatResult(n) {
        // Round to 10 decimal places to suppress floating-point noise
        return String(Math.round(n * 1e10) / 1e10);
    }

    // ── Safe recursive-descent expression evaluator (no eval) ───────────────

    function tokenize(expr) {
        var tokens = [];
        var i = 0;
        while (i < expr.length) {
            var ch = expr.charAt(i);
            if (/[\d.]/.test(ch)) {
                var num = '';
                while (i < expr.length && /[\d.]/.test(expr.charAt(i))) {
                    num += expr.charAt(i++);
                }
                tokens.push({ type: 'NUM', value: parseFloat(num) });
            } else if (isOperator(ch)) {
                tokens.push({ type: 'OP', value: ch });
                i++;
            } else {
                i++;
            }
        }
        return tokens;
    }

    var tpos;

    function parsePrimary(tokens) {
        if (tpos < tokens.length && tokens[tpos].type === 'NUM') {
            return tokens[tpos++].value;
        }
        throw new Error('invalid_expr');
    }

    function parseUnary(tokens) {
        if (tpos < tokens.length && tokens[tpos].type === 'OP' && tokens[tpos].value === '-') {
            tpos++;
            return -parsePrimary(tokens);
        }
        return parsePrimary(tokens);
    }

    function parseMulDiv(tokens) {
        var left = parseUnary(tokens);
        while (tpos < tokens.length && (tokens[tpos].value === '*' || tokens[tpos].value === '/')) {
            var op = tokens[tpos++].value;
            var right = parseUnary(tokens);
            if (op === '/') {
                if (right === 0) { throw new Error('div_zero'); }
                left = left / right;
            } else {
                left = left * right;
            }
        }
        return left;
    }

    function parseAddSub(tokens) {
        var left = parseMulDiv(tokens);
        while (tpos < tokens.length && (tokens[tpos].value === '+' || tokens[tpos].value === '-')) {
            var op = tokens[tpos++].value;
            var right = parseMulDiv(tokens);
            left = op === '+' ? left + right : left - right;
        }
        return left;
    }

    function evaluate(expr) {
        var tokens = tokenize(expr);
        if (tokens.length === 0) { throw new Error('empty'); }
        tpos = 0;
        var result = parseAddSub(tokens);
        if (tpos < tokens.length) { throw new Error('invalid_expr'); }
        return result;
    }

    // ── History (max 5, FIFO) ────────────────────────────────────────────────

    function renderHistory() {
        var $list = $('#calc-history-list');
        $list.empty();
        if (history.length === 0) {
            $list.append('<li class="calc-history-empty">No history yet.</li>');
            return;
        }
        for (var i = 0; i < history.length; i++) {
            $list.append($('<li/>').text(history[i]));
        }
    }

    function addToHistory(entry) {
        history.unshift(entry);
        if (history.length > 5) { history.pop(); }
        renderHistory();
    }

    // ── Button click handler ─────────────────────────────────────────────────

    $('.calc-grid button').on('click', function () {
        var val = String($(this).data('value'));

        if (val === 'C') {
            expression = '';
            justCalculated = false;
            updateDisplay('');
            return;
        }

        if (val === '=') {
            if (expression === '') { return; }
            try {
                var result = evaluate(expression);
                var resultStr = formatResult(result);
                addToHistory(expression + ' = ' + resultStr);
                expression = resultStr;
                justCalculated = true;
                updateDisplay(expression);
            } catch (e) {
                updateDisplay(e.message === 'div_zero' ? 'Error: Div/0' : 'Error');
                expression = '';
                justCalculated = false;
            }
            return;
        }

        // After a completed calculation, operator continues from result; digit resets
        if (justCalculated) {
            justCalculated = false;
            if (!isOperator(val)) { expression = ''; }
        }

        // Replace trailing operator with new operator
        if (isOperator(val) && expression.length > 0 && isOperator(expression.charAt(expression.length - 1))) {
            expression = expression.slice(0, -1);
        }

        // Disallow leading operator except unary minus
        if (isOperator(val) && expression === '' && val !== '-') { return; }

        // Prevent duplicate decimal point in the current number token
        if (val === '.') {
            var segments = expression.split(/[+\-*/]/);
            if (segments[segments.length - 1].indexOf('.') !== -1) { return; }
        }

        expression += val;
        updateDisplay(expression);
    });
});
