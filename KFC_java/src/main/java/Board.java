public class Board {
    private final int cellHPix;
    private final int cellWPix;
    private final int wCells;
    private final int hCells;
    private final Img img;

    private final double cellHM;
    private final double cellWM;

    public Board(int cellHPix, int cellWPix,
                 int wCells, int hCells,
                 Img img) {
        this(cellHPix, cellWPix, wCells, hCells, img, 1.0, 1.0);
    }

    public Board(int cellHPix, int cellWPix,
                 int wCells, int hCells,
                 Img img,
                 double cellHM, double cellWM) {
        this.cellHPix = cellHPix;
        this.cellWPix = cellWPix;
        this.wCells = wCells;
        this.hCells = hCells;
        this.img = img;
        this.cellHM = cellHM;
        this.cellWM = cellWM;
    }

    /* ------------ convenience ------------- */

    public Board cloneBoard() {
        Img newImg;
        if (img != null && img.get() != null) {
            java.awt.image.BufferedImage copy = new java.awt.image.BufferedImage(
                    img.get().getColorModel(),
                    img.get().copyData(null),
                    img.get().isAlphaPremultiplied(),
                    null);
            BuffImg bi = new BuffImg();
            bi.setBufferedImage(copy);
            newImg = bi;
        } else {
            newImg = new BuffImg();
        }
        return new Board(cellHPix, cellWPix, wCells, hCells, newImg, cellHM, cellWM);
    }

    public void show() { if (img != null) img.show(); }

    /* ------------ conversions ------------- */

    /** Convert (x, y) in metres to board cell (row, col). */
    public int[] mToCell(double xM, double yM) {
        int col = (int) Math.round(xM / cellWM);
        int row = (int) Math.round(yM / cellHM);
        return new int[]{row, col};
    }

    public Moves.Pair mToCellPair(double xM, double yM) {
        int col = (int) Math.round(xM / cellWM);
        int row = (int) Math.round(yM / cellHM);
        return new Moves.Pair(row, col);
    }

    /** Convert a cell (row, col) to its top-left corner in metres. */
    public double[] cellToM(int row, int col) {
        return new double[]{col * cellWM, row * cellHM};
    }

    public double[] cellToM(Moves.Pair cell) {
        return cellToM(cell.r, cell.c);
    }

    /** Convert (x, y) in metres to pixel coordinates. */
    public int[] mToPix(double xM, double yM) {
        int xPx = (int) Math.round(xM / cellWM * cellWPix);
        int yPx = (int) Math.round(yM / cellHM * cellHPix);
        return new int[]{xPx, yPx};
    }

    /* ------------ getters ------------- */
    public int getCellHPix() { return cellHPix; }
    public int getCellWPix() { return cellWPix; }
    public int getWCells() { return wCells; }
    public int getHCells() { return hCells; }
    public Img getImg() { return img; }
} 