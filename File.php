<?php
#########################
//implementation of File.php used for test.php script from task no.2 from IPP
//autor: Jakub Sokolik (xsokol14)
//13.3.2021
#########################
require_once("./HtmlGen.php");

class File{

    var $name;
    function __construct($filename){
        $this->name = strstr($filename, ".src", true);
        $this->FileCheck(".in");
        $this->FileCheck(".out");
        $this->FileCheck(".rc", true);
    }

    //function check all file, if any is missig, there create it
    private function FileCheck($suffix, $write = false){
      if (!file_exists($this->name.$suffix)){
        $file = fopen($this->name.$suffix, 'w+');
        if ($write) fwrite($file, "0");
        fclose($file);
      }
    }
}


class Search{

    // function for find all .src files
    public function FindFiles($dir, $recursive){

      if ($recursive){
        $directory = new RecursiveDirectoryIterator($dir);
        $iterator = new RecursiveIteratorIterator($directory);

        foreach ($iterator as $filename) {
          if (preg_match('/.*\.src$/', $filename)){
            yield $filename->__toString();
          }
        }
      }else{
        foreach (glob("$dir/*.src") as $filename){
            yield $filename;
        }
      }
    }
}

 ?>
