#509 occluder rejection certificate

The reference is508: its active-y polygon Union is enabled,509 is disabled.
The candidate enables only509 in addition. Input and output area definitions,
cell clipping, original three occluder-edge clips, alpha interval handling and
fragment subtraction remain unchanged whenever the certificate is uncertain.

The existing input contract supplies finite projected triangle vertices,
their actual coordinate bounds and affine depth planes from the same pose.
The optimization does not group same-role triangles into a surface.

For each actual cell-clipped hair polygon p, build the coordinate box of its
stored vertices. This is already the result of the original cell clipping;
no ideal/pre-clip box is substituted. The box is expanded only by a derived
binary64 roundoff enclosure for the following three `Overlap` clips.

Let u=2^-52, a conservative bound on round-to-nearest relative error, and
eta=2^-1074. For finite arithmetic, |fl(q)-q|<=u|q|+eta. Consider the original
coordinate interpolation fl(a+fl(fl(b-a)*t)), |a|,|b|<=M, M>=1,0<=t<=1.
The subtraction, product and final addition errors are bounded respectively by

    e1 <=2uM+eta
    e2 <=u(2M+e1)+eta
    e3 <=u(3M+e1+e2)+eta.

Their total is at most(7u+6u²+2u³)M+(3+3u+u²)eta, less than16uM.
The exact convex interpolation lies between a and b. Copies remain in the
same box; each new intersection can exceed it only by that bound. After the
three clips the cumulative expansion is at most

    M((1+16u)^3-1) <64uM =2^-46 M.

Multiplication of M>=1 by the power of two2^-46 is exact in this guarded
range. NextDown/NextUp after subtracting/adding the bound encloses the final
box endpoints outward. This constant is a roundoff bound, not a tuned geometry
or depth tolerance. The candidate does not shrink to the ideal occluder/cell
intersection, which could exclude computed vertices by rounding.

The numeric guard maxCoordinate<=sqrt(Double.MaxValue/64) ensures original
triangle-edge coefficients/evaluations and opposite-sign clip denominators
remain finite, including the small expansion above. Opposite-signed finite
da/db therefore give a computed t=da/(da-db) within[0,1]. This argument does
not assume the edge classification matches an ideal curve; it encloses the
actual reference arithmetic either way. Nonfinite or out-of-range coordinates
and depth coefficients retain the reference path.

Compute exactly the same rounded coefficients as the later original depth clip:

    D(x,y)=(hair.z.x-other.z.x)*x
          +(hair.z.y-other.z.y)*y
          +(hair.z.c-other.z.c).

On the expanded box choose each coordinate endpoint according to the sign of
its coefficient. Each product, their sum and the constant addition are bounded
outward using the next representable double. This upper bound encloses the
original floating evaluation at every computed overlap vertex. An uncertain
bound, equality or nonnegative upper bound does not reject the triangle.

If the certified upper bound is strictly negative, all vertices supplied to
the original positive depth clip would have da/db<0. It would append no vertex,
return an empty polygon and hit the existing area-zero continue before any
alpha or subtraction operation. Skipping directly is therefore equivalent for
both lower/upper areas, independent of the occluder's opacity. No epsilon,
occlusion disable, source-alpha change or nearest-surface assumption is added.

This mathematical argument complements the existing six509 certificates/
fallback checks, six reference geometry/alpha/depth fixtures, saved81-input
bit/mask comparison and conditional runtime checks. It is not a speed claim.
