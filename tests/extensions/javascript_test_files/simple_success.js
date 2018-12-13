/* .. pii:: Group 1 - Annotation 1 */
// .. pii_types:: id, name
// .. pii_retirement:: local_api, consumer_api

'use strict';

/* .. no_pii:: No Group 1 */
var foo = require('foo');

var bar = [
    something.check('foo', 'narf'),
    /foo\/js/,
    /*
    .. pii:: Group 2 - Annotation 1 comment is a
    multi line comment
    */
    // .. pii_types:: id, name
    // .. pii_retirement:: local_api, consumer_api
    /pii\/js/,
    // .. pii:: Group 3 - Annotation 1
    // .. pii_types:: id, name
// .. pii_retirement:: local_api, consumer_api
    /common\/lib\/xmodule\/xmodule\/js\/src\//
];

something.pii = SomethingElse.do_it({
    // .. no_pii:: No Group 2

    context: "nothing",

    taco: {
        Foo: 'just another pii'
    }
}); // .. no_pii:: No Group 3

/*
Text above token

.. pii:: Group 4 - Annotation 1
.. pii_types:: id, name
.. pii_retirement:: local_api, consumer_api

Text below token
*/

// These check different ways of doing options
// .. ignored:: silly-silly,terrible, irrelevant
// .. ignored:: terrible irrelevant silly-silly

/* .. pii:: Group 5 - Annotation 1
.. pii_types:: id, name
.. pii_retirement:: local_api, consumer_api */

/*
* .. pii:: Group 6 - Annotation 1
* .. pii_types:: id, name
* .. pii_retirement:: local_api, consumer_api
*/

/*.. pii:: Group 7 - Annotation 1
.. pii_types:: id, name
.. pii_retirement:: local_api, consumer_api*/
