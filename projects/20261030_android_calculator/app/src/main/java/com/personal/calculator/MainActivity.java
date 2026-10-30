package com.personal.calculator;

import android.app.Activity;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.math.BigDecimal;
import java.math.RoundingMode;

public class MainActivity extends Activity {
    private String first = "";
    private String second = "";
    private String operator = "";
    private String message = "";
    private boolean finished = false;
    private TextView display;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        if (state != null) {
            first = state.getString("first", "");
            second = state.getString("second", "");
            operator = state.getString("operator", "");
            message = state.getString("message", "");
            finished = state.getBoolean("finished");
        }
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        int padding = (int) (16 * getResources().getDisplayMetrics().density);
        root.setPadding(padding, padding, padding, padding);
        display = new TextView(this);
        display.setTextSize(32);
        display.setGravity(Gravity.END | Gravity.CENTER_VERTICAL);
        display.setTextIsSelectable(true);
        root.addView(display, new LinearLayout.LayoutParams(-1, 0, 2));
        String[][] rows = {{"C", "DEL", "÷"}, {"7", "8", "9", "×"},
                {"4", "5", "6", "−"}, {"1", "2", "3", "+"}, {"0", ".", "="}};
        for (String[] row : rows) {
            LinearLayout line = new LinearLayout(this);
            for (String label : row) {
                Button button = new Button(this);
                button.setText(label);
                button.setTextSize(22);
                button.setAllCaps(false);
                button.setOnClickListener(v -> press(label));
                line.addView(button, new LinearLayout.LayoutParams(0, -1, 1));
            }
            root.addView(line, new LinearLayout.LayoutParams(-1, 0, 1));
        }
        setContentView(root);
        refresh();
    }

    @Override protected void onSaveInstanceState(Bundle state) {
        super.onSaveInstanceState(state);
        state.putString("first", first);
        state.putString("second", second);
        state.putString("operator", operator);
        state.putString("message", message);
        state.putBoolean("finished", finished);
    }

    private void press(String key) {
        if (key.equals("C")) {
            first = second = operator = message = "";
            finished = false;
        } else if (!message.isEmpty()) {
            return;
        } else if (key.equals("DEL")) {
            if (finished) finished = false;
            if (!second.isEmpty()) second = second.substring(0, second.length() - 1);
            else if (!operator.isEmpty()) operator = "";
            else if (!first.isEmpty()) first = first.substring(0, first.length() - 1);
            if (first.equals("-")) first = "";
        } else if (key.equals("=")) {
            calculate();
        } else if (key.equals("+") || key.equals("−") || key.equals("×") || key.equals("÷")) {
            if (!first.isEmpty() && second.isEmpty()) {
                operator = key;
                finished = false;
            }
        } else {
            if (finished) {
                first = second = operator = "";
                finished = false;
            }
            String value = operator.isEmpty() ? first : second;
            if (key.equals(".") && value.contains(".")) return;
            if (key.equals(".") && value.isEmpty()) value = "0";
            value += key;
            if (operator.isEmpty()) first = value; else second = value;
        }
        refresh();
    }

    private void calculate() {
        if (first.isEmpty() || operator.isEmpty() || second.isEmpty()) return;
        BigDecimal a = new BigDecimal(first);
        BigDecimal b = new BigDecimal(second);
        BigDecimal result;
        switch (operator) {
            case "+": result = a.add(b); break;
            case "−": result = a.subtract(b); break;
            case "×": result = a.multiply(b); break;
            default:
                if (b.signum() == 0) {
                    message = "Cannot divide by zero. Tap C to clear.";
                    return;
                }
                result = a.divide(b, 12, RoundingMode.HALF_UP);
        }
        first = result.stripTrailingZeros().toPlainString();
        second = operator = "";
        finished = true;
    }

    private void refresh() {
        display.setText(message.isEmpty() ? (first + " " + operator + " " + second).trim() : message);
    }
}
