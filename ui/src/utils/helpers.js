//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 18.02.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
// Make id
//------------------------------------------------------------------------------
export function makeId(length) {
  var text = '';
  var possible = 'abcdefghijklmnopqrstuvwxyz0123456789';

  for(var i = 0; i < length; i++)
    text += possible.charAt(Math.floor(Math.random() * possible.length));

  return text;
}

//------------------------------------------------------------------------------
// Capitalize first letter
//------------------------------------------------------------------------------
export function capitalizeFirst(str) {
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

//------------------------------------------------------------------------------
// Validate scheduling spec
//------------------------------------------------------------------------------
export function scheduleValid(spec) {
  //----------------------------------------------------------------------------
  // Now is a valid spec
  //----------------------------------------------------------------------------
  if(spec === 'now')
    return true;

  //----------------------------------------------------------------------------
  // Check the directives
  //----------------------------------------------------------------------------
  let directives = spec.toLowerCase().split(' ');
  if(directives.length === 0)
    return false;

  if(directives[0] !== 'every')
    return false;

  if(directives.length < 2)
    return false;

  //----------------------------------------------------------------------------
  // Check the interval
  //----------------------------------------------------------------------------
  const interval = parseInt(directives[1], 10);
  if(!isNaN(interval)) {
    if(directives.length < 3)
      return false;
    directives = directives.slice(2);
  }
  else
    directives = directives.slice(1);

  //----------------------------------------------------------------------------
  // Check the directives
  //----------------------------------------------------------------------------
  const directive_names = [
    'second', 'seconds', 'minute', 'minutes', 'hour', 'hours', 'day', 'days',
    'week', 'weeks', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
    'saturday', 'sunday', 'at', 'to'];
  directives = directives.reverse();

  while(directives.length) {
    //--------------------------------------------------------------------------
    // Check the directive
    //--------------------------------------------------------------------------
    const directive = directives.pop();
    if(directive_names.indexOf(directive) < 0)
      return false;

    //--------------------------------------------------------------------------
    // Check the argument to "to"
    //--------------------------------------------------------------------------
    if(directive === 'to') {
      if(!directives.length)
        return false;
      let arg = directives.pop();
      arg = parseInt(arg, 10);
      if(isNaN(arg))
        return false;
    }
    //--------------------------------------------------------------------------
    // Check the argument to "at"
    //--------------------------------------------------------------------------
    else if(directive === 'at') {
      if(!directives.length)
        return false;
      let arg = directives.pop();
      let argSplit = arg.split(':');
      if(argSplit.length !== 2)
        return false;
      arg = parseInt(argSplit[0], 10);
      if(isNaN(arg))
        return false;
      arg = parseInt(argSplit[1], 10);
      if(isNaN(arg))
        return false;
    }
  }

  return true;
}

//------------------------------------------------------------------------------
// Validate payload
//------------------------------------------------------------------------------
export function payloadValid(str) {
  var obj = null;
  try {
    obj = JSON.parse(str);
  } catch (e) {
    return false;
  }
  if (typeof obj === 'object' && obj !== null) {
    return true;
  }
  return false;
}
