/* 
 * JSChannel (https://github.com/mozilla/jschannel) will be loaded prior to this
 * script. We will use it use to let JSInput call 'gradeFn', and eventually 
 * 'stateGetter' & 'stateSetter' in the iframe's content even if it hasn't the 
 * same origin, therefore bypassing SOP:
 * https://developer.mozilla.org/en-US/docs/Web/JavaScript/Same_origin_policy_for_JavaScript
 */    

var JSInput = (function ($, undefined) {
    // Initialize js inputs on current page.
    // N.B.: No library assumptions about the iframe can be made (including,
    // most relevantly, jquery). Keep in mind what happens in which context
    // when modifying this file.

    // When all the problems are first loaded, we want to make sure the
    // constructor only runs once for each iframe; but we also want to make
    // sure that if part of the page is reloaded (e.g., a problem is
    // submitted), the constructor is called again.

    /*                      Utils                               */


    // Take a string and find the nested object that corresponds to it. E.g.:
    //    deepKey(obj, "an.example") -> obj["an"]["example"]
    var _deepKey = function(obj, path){
        for (var i = 0, p=path.split('.'), len = p.length; i < len; i++){
            obj = obj[p[i]];
        }
        return obj;
    };


    /*      END     Utils                                   */


    function jsinputConstructor(elem) {
        // Define an class that will be instantiated for each jsinput element
        // of the DOM

        /*                      Private methods                          */

        var sect = $(elem).parent().find('section[class="jsinput"]');
        var sectAttr = function (e) { return $(sect).attr(e); };
        var iframe = $(elem).find('iframe[name^="iframe_"]').get(0);
        var cWindow = iframe.contentWindow;
        var path = iframe.src.substring(0, iframe.src.lastIndexOf("/")+1);
        // Get the hidden input field to pass to customresponse
        var inputField = $(elem).parent().find('input[id^="input_"]');
        // Get the grade function name
        var getGradeFn = sectAttr("data");
        // Get state getter
        var getStateGetter = sectAttr("data-getstate");
        // Get state setter
        var getStateSetter = sectAttr("data-setstate");
        // Get stored state
        var getStoredState = sectAttr("data-stored");
        // Bypass single-origin policy only if this attribute is "false"
        // In that case, use JSChannel to do so.
        var sop = sectAttr("data-sop"); 
        sop = (sop !== "false");

        var channel;
        if (!sop) {
            channel = Channel.build({
                window: cWindow,
                origin: path,
                scope: "JSInput",
                onReady: function() {
                }
            });
         }   

        /*                       Public methods                     */
        
        // Only one public method that updates the hidden input field.
        var update = function (callback) {
            var ans, state, store;

            if (sop) {
                ans = _deepKey(cWindow, gradeFn)();
                // setstate presumes getstate, so don't getstate unless setstate
                // is defined.
                if (getStateGetter && getStateSetter) {
                    state = unescape(_deepKey(cWindow, getStateGetter)());
                    store = {
                        answer: ans,
                        state:  state
                    };
                    inputField.val(JSON.stringify(store));
                } else {
                    inputField.val(ans);
                }
                callback();
            } else {
                channel.call({
                    method: "getGrade",
                    params: "",
                    success: function(val) {
                        ans = decodeURI(val.toString());

                        // setstate presumes getstate, so don't getstate unless 
                        // setstate is defined.
                        if (getStateGetter && getStateSetter) {
                            channel.call({
                                method: "getState",
                                params: "",
                                success: function(val) {
                                    state = decodeURI(val.toString());
                                    store = {
                                        answer: ans,
                                        state:  state
                                    };
                                    inputField.val(JSON.stringify(store));
                                    callback();
                                }
                            });
                        } else {
                            inputField.val(ans);
                            callback();
                        }
                    }
                });
            }
        };

        /*                      Initialization                          */

        var gradeFn = getGradeFn;

        // Put the update function as the value of the inputField's "waitfor"
        // attribute so that it is called when the check button is clicked.
        inputField.data('waitfor', update);

        // Check whether application takes in state and there is a saved
        // state to give it. If getStateSetter is specified but calling it
        // fails, wait and try again, since the iframe might still be
        // loading.
        if (getStateSetter && getStoredState) {
            var sval, jsonVal;

            try {
              jsonVal = JSON.parse(getStoredState);
            } catch (err) {
              jsonVal = getStoredState;
            }

            if (typeof(jsonVal) === "object") {
                sval = jsonVal["state"];
            } else {
                sval = jsonVal;
            }

            // Try calling setstate every 200ms while it throws an exception,
            // up to five times; give up after that.
            // (Functions in the iframe may not be ready when we first try
            // calling it, but might just need more time. Give the functions
            // more time.)
            function whileloop(n) {
                if (n < 5){
                    try {
                        if (sop) {
                            _deepKey(cWindow, getStateSetter)(sval);
                        } else {
                            channel.call({
                                method: "setState",
                                params: sval,
                                success: function(v) {
                                }
                            });
                        }
                    } catch (err) {
                        setTimeout(whileloop(n+1), 200);
                    }
                }
                else {
                    console.debug("Error: could not set state");
                }
            }
            whileloop(0);
        }
    }

    function walkDOM() {
        var dataProcessed, all;

        // Find all jsinput elements
        all = $(document).find('section[class="jsinput"]');

        // When a JSInput problem loads, its data-processed attribute is false,
        // so the jsconstructor will be called for it.
        // The constructor will not be called again on subsequent reruns of
        // this file by other JSInput. Only if it is reloaded, either with the
        // rest of the page or when it is submitted, will this constructor be
        // called again. 
        all.each(function(index, value) {
            dataProcessed = ($(value).attr("data-processed") === "true");
            if (!dataProcessed) {
                jsinputConstructor(value);
                $(value).attr("data-processed", 'true');
            }
        });
    }

    // This is ugly, but without a timeout pages with multiple/heavy jsinputs
    // don't load properly.
    if ($.isReady) {
        setTimeout(walkDOM, 300);
    } else {
        $(document).ready(setTimeout(walkDOM, 300));
    }

    return {
        jsinputConstructor: jsinputConstructor,
        walkDOM: walkDOM
    };
    
})(window.jQuery);