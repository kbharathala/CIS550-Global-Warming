var express = require('express');
var mysql = require('mysql');
var router = express.Router();

var connection = mysql.createConnection({
  host: 'proj1.ci4g2wbj7lrc.us-west-2.rds.amazonaws.com',
  user: 'rip_us',
  password: 'abdu9000',
  database: 'proj'
});

connection.connect();

/* GET home page. */
router.get('/', function(req, res, next) {
  res.render('index', { title: 'Express' });
});

router.get('/country/:country', function(req, res, next) {
  var country_name = req.params["country"];
  var query = 'SELECT * from Country C where C.Name = \"' + country_name + '\";'
  console.log(query);
  var result = null;
  connection.query(query, function(error, results, fields) {
    if (error) throw error;
    console.log(results);
    console.log(results[0]);
    result = results[0];
    res.render('country', {country: result});
  });
  /*if (result != null) {
    console.log("here");
    res.render('country', {country: result});
  }
  else {
    console.log("here2");
    res.render('index', {title: country_name});
  }*/
});

module.exports = router;