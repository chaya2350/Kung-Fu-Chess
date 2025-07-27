
import java.awt.*;

public class Example {
    public static void main(String[] args) throws Exception {

        String bg   = "../pieces/board.png";   // put any image path here
        String logo = "../pieces/QW/states/jump/sprites/2.png";         // PNG with transparency

        Img canvas = new BuffImg().read(bg);                                          // keep full size
        Img badge  = new BuffImg().read(logo,
                                    new Dimension(200, 200), true, null);        // shrink

        badge.putText("Demo", 10, 30, 1.2f,
                      new Color(255, 60, 60, 255), 0);

        badge.drawOn(canvas, 40, 40);
        canvas.show();
    }
}
