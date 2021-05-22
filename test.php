<?php
#########################
//implementation of test.php script from task no.2 from IPP
//autor: Jakub Sokolik (xsokol14)
//13.3.2021
#########################
require_once("./File.php");
require_once("./Tester.php");


######## ERROR VALUES ########
ini_set('display_errors', 'stderr');
define("INVALID_FILE", 41);
define("ARGS_ERR", 10);

############## DEFINITION OF VAR #################
$path = getcwd();
$parser = "parse.php";
$interpreter = "interpret.py";
$jexamxml = "/pub/courses/ipp/jexamxml/jexamxml.jar";
$jexamcnfg = "/pub/courses/ipp/jexamxml/options";
$match ="*";
$recursive = false;
$parse_only = false;
$int_only = false;
$test_both = false;
$totalfail = 0;
$totalpass = 0;
$dirlist = [];
$filelist = [];
$regex ="/.*/";


############ DEFINITION OF FUNCTINS ###############
function usage(){
  echo "Usage: test.php [options]\n";
  echo("[options]:\n
  --help -> show usage\n
  --directory=path -> set directory where are store tests\n
  --recursive -> used for run tests stored in subdirectories\n
  --parse-script=file -> set file where is parse.php script\n
  --int-script=file -> set file where is interpreter.py script\n
  --jexamxml=file -> set file where is jexamxml script, used for make diff of XML code\n
  --jexamcnfg-script=file -> set file where are options for jexamxml script\n
  --parse-only -> used for tests only parse.php script, defaul set check both scripts\n
  --int-only -> used for tests only interpreter.py script, defaul set check both scripts\n");
  exit(0);
}

function CheckFiles($dir, $parser, $interpreter, $jexamxml, $jexamcnfg){
  $return = false;

  if(!is_dir($dir)) $return = true;
  if(!file_exists($parser)) $return = true;
  if(!file_exists($interpreter)) $return = true;
  if(!file_exists($jexamxml)) $return = true;
  if(!file_exists($jexamcnfg)) $return = true;

  if ($return){
    fwrite(STDERR, "Invalid file/directory was entry" . PHP_EOL);
    exit(INVALID_FILE);
  }
}

// function sort testlist to list of file and list of dir
function SortTestList($path, &$dirlist, &$filelist){
  $testlist = file($path);

  foreach ($testlist as $item) {
    $item = realpath(preg_replace('/\\n/', '', $item));

    if (is_dir($item)) {
      if (!in_array($item, $dirlist)) array_push($dirlist, $item);
      continue;
    }
    if (file_exists($item)){
       if (!in_array($item, $filelist)) array_push($filelist, $item);
       continue;
    }

    echo "Invalid file/directory was entry\n";
    exit(INVALID_FILE);
  }
}

function RunTests($file){

}

############# OPTIONS PROCESSING ################
$longopts = array(
  "directory::",
  "testlist::",
  "match::",
  "parse-script::",
  "int-script::",
  "jexamxml::",
  "jexamcnfg::",
  "recursive",
  "help",
  "parse-only",
  "int-only",);

$options = getopt("", $longopts);

if (array_key_exists("help", $options)) usage();
if (array_key_exists("parse-script", $options)) $parser = realpath($options["parse-script"]);
if (array_key_exists("int-script", $options)) $interpreter = realpath($options["int-script"]);
if (array_key_exists("jexamxml", $options)) $jexamxml = realpath($options["jexamxml"]);
if (array_key_exists("jexamcnfg", $options)) $jexamcnfg = realpath($options["jexamcnfg"]);
if (array_key_exists("directory", $options)) {
  $path = realpath($options["directory"]);
  array_push($dirlist, $path);
  if (array_key_exists("testlist", $options)){
    fwrite(STDERR, "You can't use --dierectory and --testlist in same time" . PHP_EOL);
    exit (ARGS_ERR);
  }
}
if (!array_key_exists("directory", $options) && !array_key_exists("testlist", $options)) array_push($dirlist, $path);
if (array_key_exists("match", $options)) $regex = $options["match"];
if (!preg_match('/\/.*\//', $regex)) $regex = "/$regex/";
if (array_key_exists("testlist", $options)) {
  $testlist = realpath($options["testlist"]);
  SortTestList($testlist, $dirlist, $filelist);
}
if (array_key_exists("parse-only", $options)) $parse_only = true;
if (array_key_exists("int-only", $options)) $int_only = true;
if (!$parse_only && !$int_only) $test_both = true;
if (array_key_exists("recursive", $options)) $recursive = true;

############## MAIN #######################
CheckFiles($path, $parser, $interpreter, $jexamxml, $jexamcnfg);

//search file.src and add in array $filelist
$searcher = new Search();
foreach($dirlist as $dir){
  foreach ($searcher->FindFiles($dir, $recursive) as $filename) {
    if (!in_array($filename, $filelist)) array_push($filelist, $filename);
  }
}

foreach ($filelist as $filename) {
  if (preg_match('/.*\.src$/', $filename)){

    $file = new File($filename);
    $test = new Tester($file);

    //echo "$test->name\n";
    //fwrite(STDERR, "$file->name\n");
    if (preg_match($regex, "$test->name.src")){

      if ($parse_only) $isOk = $test->ParseOnly($file, $parser, $jexamxml, $jexamcnfg);
      if ($int_only) $isOk = $test->InterpreterOnly($file, $interpreter);

      if ($test_both) $isOk = $test->TestBoth($file, $parser, $interpreter, $jexamxml, $jexamcnfg);

      if ($isOk == true){
        $htmlpass = $htmlpass . $test->htmlout;
        $totalpass++;
      }else{
        $htmlfail = $htmlfail . $test->htmlout;
        $totalfail++;
      }
    }
  }
}

HtmlGen::GetHtml($totalpass, $totalfail, $htmlpass, $htmlfail);
exit(0);
?>
