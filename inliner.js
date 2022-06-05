var juice = require('juice');
var fs = require('fs');
console.log(juice(fs.readFileSync(process.argv[2], "utf8")));
