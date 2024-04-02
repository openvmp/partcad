module hexagonal_prism(length = 10) {
    h = sqrt(3)*length;
    cylinder(h=length, r = h*0.5, $fn=6);
}

hexagonal_prism();