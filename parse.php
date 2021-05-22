<?php
#########################
//implementation of task no.1 from IPP
//autor: Jakub Sokolik (xsokol14)
//13.3.2021
#########################


######## ERROR VALUES ########
define("ARGS_ERR", 10);
define("FILE_WRITE_ERR", 12);
define("HEADER_ERR", 21);
define("OPCODE_ERR", 22);
define("OTHERS_ERR", 23);

ini_set('display_errors', 'stderr');



########### DEFINITION OF FUNCTIONS ##########
//if insert variable is string represent a valid variable return true
function isvar($var){
  if (preg_match("/^(LF|GF|TF)@[a-zA-Z_\-$&%*!?][a-zA-Z_\-$&%*!?0-9]*$/", $var)){
    return true;
  }
  return false;
}

//if insert variable is string represent a valid label return true
function islabel($var){
  if (preg_match('/^[a-zA-Z_\-$&%*!?][a-zA-Z_\-$&%*!?0-9]*$/', $var)){
    return true;
  }
  return false;
}

//if insert variable is string represent a valid variable, string, bool, int, nil return true
function issym($var){
  if (isvar($var)){
    return true;
  }
  //string
  if (preg_match('/^(string)@(?:[\x21-\x22\x24-\x5B\x5D-\x7EÁ-ž]|\\\\[0-9]{3})*$/', $var)){
      return true;
  }
  //bool
  if (preg_match('/(bool)@((false)|(true))$/', $var)){
    return true;
  }
  //nil
  if (preg_match('/(nil)@(nil)$/', $var)){
    return true;
  }
  //int
  if (preg_match('/(int)@[-+]{0,1}[0-9]+$/', $var)){
    return true;
  }
  return false;
}

//if insert variable is string represent a valid type return true
function istype($var){

  if (preg_match('/^((bool)|(int)|(nil)|(string))$/', $var)){
    return true;

  }
  return false;
}

//if insert variable content only white characters return true
function iswhite($var){
  if(preg_match('/^[\x01-\x20\x7F]*$/', $var)){
    return true;
  }
  return false;
}

//if $trim=true, function throw comments and return string without comm.
//if $trim=false, function return count of trimed comments (for STATP)
function throwcom($var, $trim){
  static $counter = 0;
  if ($trim){
    $splited = explode('#', trim($var, "\n"));
    if(!$splited[1] == null){
      $counter ++;
    }
    return trim($splited[0]);
  }
  return $counter;

}

//function check validity of inserts ARGUMENTS
//in case of --help argument, printed usage message and finish program with 0.
function checkopt($argv){
  if(in_array("--help", $argv)){
    echo("Usage: parse.php [options] <input_file\n");
    echo("[options]:\n
    --help -> show usage\n
    --stats=file -> set file where will store stats\n
    \t -> in file will store stats thats set after --stats arg\n
    \t -> more --stats can be used, but files must be diferent\n
    --loc -> used for count lines with instructions\n
    --comments -> used for count lines with comments\n
    --labels -> used for count defined labels\n
    --jumps -> used for count a jump instructions\n
    --fwjumps -> used for count forward jumps\n
    --backjumps -> used for count a back jumps\n
    --badjumps -> used for count jumps to undefined label\n");
    exit(0);
  }
  if ($argv == 1){
    return;
  }
  $files = [];
  foreach ($argv as &$value) {
    if (count($files) == 0){
      if (preg_match("/^--(loc|comments|label|jumps|fwjumps|backjumps|badjumps)$/", $value)){
        exit(ARGS_ERR);
      }
    }
    if (preg_match("/^--stats(?<name>.*)/", $value, $matches)){
      if (in_array($matches["name"], $files)){
        exit(FILE_WRITE_ERR);
      }
      array_push($files, $matches["name"]);
    }

  }
}

//function replace problmatic char for XML like < > &.
function problemchar($var){
  return preg_replace(["/&/", "/</", "/>/",], ["&amp;", "&lt;", "&gt;"], $var);

}
//function remove all '' from array
//this is used after exploding instructions, where is checking size of arry
function removespaces(&$arr){
  while(in_array('',$arr)){
    array_splice($arr, array_search('', $arr), 1);
  }
}


####### VARIABLES INITIALIZATION #########
$label = 0;
$jumps = 0;
$fwjumps = 0;
$backjumps = 0;
$singlabel = [];
$unsinglabel = [];
$order = 0;




####### CHECK VALIDITY OF ARGUMENTS ######
checkopt($argv);



###### CHECK .IPPcode21 HEADER #######
//comments befor header are alowed. function() throwcom throw comments.
//white character befor header are alowed too, function iswhite() check it.
$header = false;
while ($line = fgets(STDIN)){
  $withoutcomm = throwcom($line, true);
  if (!iswhite($withoutcomm)){
    if (strcmp(strtoupper($withoutcomm), ".IPPCODE21") == 0){
      echo("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
      echo("<program language=\"IPPcode21\">\n");
      $header = true;
    }
    break;
  }
}

if(!$header) exit(HEADER_ERR);


###### CHECK INSTRUCTION CODE ########
//comments are alowed. function throwcom() throw comments.
//function isvar(), islabel(), issym() and istype chcek validity of arguments.
//function problemchar() is used for changing problmatic char for XML like < > &.
//$singlabel and $unsignlabel are used for counting fwjumps, backjumps and badjumps.
while($line = fgets(STDIN)){
  $splited = explode(' ', throwcom($line, true));
  removespaces($splited);

  switch(strtoupper($splited[0])){
    //without arg
    case 'RETURN':
      $jumps ++;
    case 'CREATEFRAME':
    case 'PUSHFRAME':
    case 'POPFRAME':
    case 'BREAK':
      if (sizeof($splited) == 1){
        $order++;
        echo("\t<instruction order=\"".$order."\" opcode=\"".strtoupper($splited[0])."\">\n");
        echo("\t</instruction>\n");
        break;
      }
      exit(OTHERS_ERR);
    //<var>
    case 'POPS':
    case 'DEFVAR':
      if (sizeof($splited) == 2){
        if (isvar($splited[1])){
          $order++;
          echo("\t<instruction order=\"".$order."\" opcode=\"".strtoupper($splited[0])."\">\n");
          echo("\t\t<arg1 type=\"var\">".problemchar($splited[1])."</arg1>\n");
          echo("\t</instruction>\n");
          break;
        }
      }
      exit(OTHERS_ERR);
    //<label>
    case 'LABEL':
      $label ++;
      if (sizeof($splited) == 2){
        if (islabel($splited[1])){
          $order++;
          echo("\t<instruction order=\"".$order."\" opcode=\"".strtoupper($splited[0])."\">\n");
          echo("\t\t<arg1 type=\"label\">".problemchar($splited[1])."</arg1>\n");
          while (in_array($splited[1], $unsinglabel)){
            unset($unsinglabel[array_search($splited[1], $unsinglabel)]);
            $fwjumps ++;
          }
          array_push($singlabel, $splited[1]);
          echo("\t</instruction>\n");
          break;
        }
      }
      exit(OTHERS_ERR);
    case 'CALL':
    case 'JUMP':
      $jumps ++;
      if (sizeof($splited) == 2){
        if (islabel($splited[1])){
          $order++;
          echo("\t<instruction order=\"".$order."\" opcode=\"".strtoupper($splited[0])."\">\n");
          echo("\t\t<arg1 type=\"label\">".problemchar($splited[1])."</arg1>\n");
          if (in_array($splited[1], $singlabel)){
            $backjumps ++;
          }else{
            array_push($unsinglabel, $splited[1]);
          }
          echo("\t</instruction>\n");
          break;
        }
      }
      exit(OTHERS_ERR);
    //<symb>
    case 'PUSHS':
    case 'WRITE';
    case 'EXIT';
    case 'DPRINT';
      if (sizeof($splited) == 2){
        if (issym($splited[1])){
          $order++;
          echo("\t<instruction order=\"".$order."\" opcode=\"".strtoupper($splited[0])."\">\n");
          $sym = explode('@', $splited[1]);
          preg_match("/(^[^@]*)@(.*$)/", $splited[1], $sym);
          if (preg_match("/(LF|GF|TF)/", $sym[1])){
            echo("\t\t<arg1 type=\"var\">".problemchar($sym[0])."</arg1>\n");
          }else{
            echo("\t\t<arg1 type=\"$sym[1]\">".problemchar($sym[2])."</arg1>\n");
          }
          echo("\t</instruction>\n");
          break;
        }
      }
      exit(OTHERS_ERR);
    //<var><symb>
    case 'MOVE':
    case 'INT2CHAR':
    case 'STRLEN':
    case 'TYPE':
    case 'NOT';
      if (sizeof($splited) == 3){
        if (isvar($splited[1]) && issym($splited[2])){
          $order++;
          echo("\t<instruction order=\"".$order."\" opcode=\"".strtoupper($splited[0])."\">\n");
          echo("\t\t<arg1 type=\"var\">".problemchar($splited[1])."</arg1>\n");
          preg_match("/(^[^@]*)@(.*$)/", $splited[2], $sym);
          if (preg_match("/(LF|GF|TF)/", $sym[1])){
            echo("\t\t<arg2 type=\"var\">".problemchar($sym[0])."</arg2>\n");
          }else{
            echo("\t\t<arg2 type=\"$sym[1]\">".problemchar($sym[2])."</arg2>\n");
          }
          echo("\t</instruction>\n");
          break;
        }
      }
      exit(OTHERS_ERR);
    //<var><type>
    case 'READ';
      if (sizeof($splited) == 3){
        if (isvar($splited[1]) && istype($splited[2])){
          $order++;
          echo("\t<instruction order=\"".$order."\" opcode=\"".strtoupper($splited[0])."\">\n");
          echo("\t\t<arg1 type=\"var\">".problemchar($splited[1])."</arg1>\n");
          echo("\t\t<arg2 type=\"type\">$splited[2]</arg2>\n");
          echo("\t</instruction>\n");
          break;
        }
      }
      exit(OTHERS_ERR);
    //<var><symb><symb>
    case 'ADD';
    case 'SUB';
    case 'MUL';
    case 'IDIV';
    case 'LT';
    case 'GT';
    case 'EQ';
    case 'AND';
    case 'OR';
    case 'STRI2INT';
    case 'CONCAT';
    case 'GETCHAR';
    case 'SETCHAR';
      if (sizeof($splited) == 4){
        if (isvar($splited[1]) && issym($splited[2]) && issym($splited[3])){
          $order++;
          echo("\t<instruction order=\"".$order."\" opcode=\"".strtoupper($splited[0])."\">\n");
          echo("\t\t<arg1 type=\"var\">".problemchar($splited[1])."</arg1>\n");
          preg_match("/(^[^@]*)@(.*$)/", $splited[2], $sym);
          if (preg_match("/(LF|GF|TF)/", $sym[1])){
            echo("\t\t<arg2 type=\"var\">".problemchar($sym[0])."</arg2>\n");
          }else{
            echo("\t\t<arg2 type=\"$sym[1]\">".problemchar($sym[2])."</arg2>\n");
          }
          preg_match("/(^[^@]*)@(.*$)/", $splited[3], $sym);
          if (preg_match("/(LF|GF|TF)/", $sym[1])){
            echo("\t\t<arg3 type=\"var\">".problemchar($sym[0])."</arg3>\n");
          }else{
            echo("\t\t<arg3 type=\"$sym[1]\">".problemchar($sym[2])."</arg3>\n");
          }
          echo("\t</instruction>\n");
          break;
        }
      }
      exit(OTHERS_ERR);
    //<label><symb><symb>
    case 'JUMPIFEQ':
    case 'JUMPIFNEQ':
      $jumps ++;
      if (sizeof($splited) == 4){
        if (islabel($splited[1]) && issym($splited[2]) && issym($splited[3])){
          $order++;
          echo("\t<instruction order=\"".$order."\" opcode=\"".strtoupper($splited[0])."\">\n");
          echo("\t\t<arg1 type=\"label\">".problemchar($splited[1])."</arg1>\n");
          if (in_array($splited[1], $singlabel)){
            $backjumps ++;
          }else{
            array_push($unsinglabel, $splited[1]);
          }
          preg_match("/(^[^@]*)@(.*$)/", $splited[2], $sym);
          if (preg_match("/(LF|GF|TF)/", $sym[1])){
            echo("\t\t<arg2 type=\"var\">".problemchar($sym[0])."</arg2>\n");
          }else{
            echo("\t\t<arg2 type=\"$sym[1]\">".problemchar($sym[2])."</arg2>\n");
          }
          preg_match("/(^[^@]*)@(.*$)/", $splited[3], $sym);
          if (preg_match("/(LF|GF|TF)/", $sym[1])){
            echo("\t\t<arg3 type=\"var\">".problemchar($sym[0])."</arg3>\n");
          }else{
            echo("\t\t<arg3 type=\"$sym[1]\">".problemchar($sym[2])."</arg3>\n");
          }
          echo("\t</instruction>\n");
          break;
        }
      }
      exit(OTHERS_ERR);
    case '':
      //after line with comm
      break;
    default:
      exit(OPCODE_ERR);
  }
}
echo ("</program>\n");



######### STATSP FILE WRITING ##########
$file = null;
foreach ($argv as &$value) {
  // if arg is stats, close old file and open new one
  if (preg_match("/^--stats=(?<name>.*)/", $value, $matches)){
    if ($file) fclose($file);
    $file = fopen($matches["name"], "w");
    if (!$file) exit(FILE_WRITE_ERR) ;

  // writing in file right value
  }elseif (preg_match("/^--(?<param>loc|comments|label|jumps|fwjumps|backjumps|badjumps)$/", $value, $matches)){
    switch($matches["param"]){
      case 'loc':
        fwrite($file, $order."\n");
        break;
      case 'comments':
        fwrite($file, throwcom("", false)."\n");
        break;
      case 'label':
        fwrite($file, $label."\n");
        break;
      case 'jumps':
        fwrite($file, $jumps."\n");
        break;
      case 'fwjumps':
        fwrite($file, $fwjumps."\n");
        break;
      case 'backjumps':
        fwrite($file, $backjumps."\n");
        break;
      case 'badjumps':
        fwrite($file, count($unsinglabel)."\n");
        break;
    }
  }
}



######## SUCESFULL END #########
if ($file) fclose($file);
exit(0);
?>
