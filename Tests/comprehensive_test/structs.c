/* Struct declarations and operations */

/* Simple struct */
struct Point {
    int x;
    int y;
};

/* Struct with multiple fields */
struct Rectangle {
    int x;
    int y;
    int width;
    int height;
};

/* Global struct */
struct Point global_point;

/* Initialize point */
void init_point(struct Point *p, int x, int y) {
    p->x = x;
    p->y = y;
}

/* Get point x coordinate */
int get_point_x(struct Point *p) {
    return p->x;
}

/* Get point y coordinate */
int get_point_y(struct Point *p) {
    return p->y;
}

/* Set point coordinates */
void set_point(struct Point *p, int x, int y) {
    p->x = x;
    p->y = y;
}

/* Calculate distance (simplified) */
int point_distance_squared(struct Point *p1, struct Point *p2) {
    int dx = p1->x - p2->x;
    int dy = p1->y - p2->y;
    return dx * dx + dy * dy;
}

/* Initialize rectangle */
void init_rectangle(struct Rectangle *r, int x, int y, int w, int h) {
    r->x = x;
    r->y = y;
    r->width = w;
    r->height = h;
}

/* Get rectangle area */
int rectangle_area(struct Rectangle *r) {
    return r->width * r->height;
}

/* Check if point is in rectangle */
int point_in_rectangle(struct Rectangle *r, struct Point *p) {
    if (p->x >= r->x && p->x < r->x + r->width) {
        if (p->y >= r->y && p->y < r->y + r->height) {
            return 1;
        }
    }
    return 0;
}

/* Move rectangle */
void move_rectangle(struct Rectangle *r, int dx, int dy) {
    r->x += dx;
    r->y += dy;
}

/* Resize rectangle */
void resize_rectangle(struct Rectangle *r, int dw, int dh) {
    r->width += dw;
    r->height += dh;
}

/* Test struct operations */
int test_struct_operations() {
    struct Point p1;
    struct Point p2;
    struct Rectangle rect;
    
    init_point(&p1, 10, 20);
    init_point(&p2, 30, 40);
    init_rectangle(&rect, 0, 0, 100, 200);
    
    int dist = point_distance_squared(&p1, &p2);
    int area = rectangle_area(&rect);
    int inside = point_in_rectangle(&rect, &p1);
    
    move_rectangle(&rect, 5, 10);
    resize_rectangle(&rect, 20, 30);
    
    return dist + area + inside;
}
