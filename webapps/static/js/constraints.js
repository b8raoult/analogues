'use strict';

function apply_constraints(U, dU, Umin, Umax, Fmin, Fmax) {


    const zero = Array.from(U, () => 0);
    const epsilon = Math.max(Math.abs(Fmin),
                             Math.abs(Fmax)) / 100000.0;

    console.log('epsilon', epsilon);
    const start = new Date();




    const elapsed = function() {
        let result = ((new Date()) - start) / 1000.0;
        if (result > 0.1) {
            console.log('elapsed');
            return true;
        }
        return false;
    }


    const add = function(a, b) {
        return Array.from(a, (x, i) => x + b[i]);
    }

    const sub = function(a, b) {
        return Array.from(a, (x, i) => x - b[i]);
    }

    const div = function(a, b) {
        return Array.from(a, (x, i) => x / b[i]);
    }

    const maximum = function(a, b) {
        return Array.from(a, (x, i) => Math.max(x, b[i]));
    }

    const square = function(a) {
        return Array.from(a, x => x * x);
        // return Array.from(a, x => Math.abs(x));

    }

    const absolute = function(a) {
        return Array.from(a, x => Math.abs(x));
    }

    const scalar_mul = function(a, b) {
        return Array.from(b, x => a * x);
    }

    const add_scalar = function(a, b) {
        return Array.from(a, x => x + b);
    }

    const div_scalar = function(a, b) {
        return Array.from(a, x => x / b);
    }

    const less_than = function(x, e) {
        return x.every(a => a <= e);
    }

    const newtons_method = function(f, x0, e) {
        let delta = absolute(f(x0));
        while (!less_than(delta, e) && !elapsed()) {
            x0 = sub(x0, div(f(x0), df(f, x0)));
            delta = absolute(f(x0));
        }
        return x0;
    }

    /* f'(x) = (f(x+e)-f(x))/e */
    const df = function(f, x) {
        let t2 = f(x)
        let t1 = f(add_scalar(x, epsilon))
        return div_scalar(sub(t1, t2), epsilon)
    }

    const minimise = function(f, x0) {
        let f_ = function(x) {
            return df(f, x);
        }
        return newtons_method(f_, x0, 1e-5);
    }

    /* Constraint x <= value */

    const less_than_constraint = function(value) {

        return function(x) {
            return square(maximum(zero, sub(x, value)));
        }
    }

    const more_than_constraint = function(value) {

        return function(x) {
            return square(maximum(zero, sub(value, x)));
        }
    }

    const add_function = function(f1, f2) {
        return function(x) {
            return add(f1(x), f2(x));
        }
    }

    // let constaints = add_function(
    //         less_than_constraint(sub(Umax, U)),
    //         more_than_constraint(sub(U, Umin)));

    // let constaints =  more_than_constraint(sub(U, Umin));
    const c_max = less_than_constraint(sub(Umax, U));

    const c_min = more_than_constraint(sub(Umin, U));


    const constaints = add_function(c_max, c_min);

    // constaints = c_min;

    const t = function(x) {

        let f = square(sub(dU, x));
        let c = constaints(x);

        return add(f, scalar_mul(w, c))
    }


    let x = dU;
    let w = 1;
    while (w < 1000 && !elapsed()) {
        x = minimise(t, x);
        w *= 1.2;
    }

    return x;

}


function test_constraints() {
    let U = [1, 2, 4, 3, 0, -1, 2, 4, 5];

    let Umax = [5, 4, 4, 4, 5, 4, 4, 4, 5];
    let Umin = [1, 0, 0, 2, 0, 0, 0, 1, 0];

    let dU = [-1, 1, 1, 1, 1, 1, 1, 1, 1];

    let _ = function(a) {
        return Array.from(a, x => Math.round(x * 100) / 100);
    }

    let check = function(x) {

        for (let i = 0; i < x.length; i++) {
            if (x[i] < 0 && Math.abs(x[i]) > 1e-2) {
                return "not ok (" + x[i] + ")";
            }
        }

        return "ok";
    }

    let apply = function(delta_u) {
        new_U = add(U, delta_u);
        console.log(' Apply', _(delta_u));
        console.log('    =>', _(new_U));
        console.log('max =>', check(sub(Umax, new_U)));
        console.log('min =>', check(sub(new_U, Umin)));

    }

    console.log('Umax', _(Umax));
    console.log('Umin', _(Umin));

    console.log('U   ', _(U));

    console.log('dU  ', _(dU));
    console.log('U+dU', _(add(U, dU)));

    console.log('x   ', _(x));
    console.log('U+x ', _(add(U, x)));


    // apply(dU);
    console.log('');
    apply(x);

}

$.apply_constraints = apply_constraints;
