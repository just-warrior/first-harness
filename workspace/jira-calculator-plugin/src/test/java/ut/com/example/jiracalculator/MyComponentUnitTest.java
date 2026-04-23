package ut.com.example.jiracalculator;

import org.junit.Test;
import com.example.jiracalculator.api.MyPluginComponent;
import com.example.jiracalculator.impl.MyPluginComponentImpl;

import static org.junit.Assert.assertEquals;

public class MyComponentUnitTest {
    @Test
    public void testMyName() {
        MyPluginComponent component = new MyPluginComponentImpl(null);
        assertEquals("names do not match!", "myComponent", component.getName());
    }
}