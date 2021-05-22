<?php
#########################
//implementation of tester.php used for test.php script from task no.2 from IPP
//autor: Jakub Sokolik (xsokol14)
//13.3.2021
#########################
class Tester{

  var $parseresult;
  var $expectedparseresult;
  var $intresult;
  var $expectedintresult;
  var $expectedresult;
  var $htmlout;
  var $name;
  var $folder;
  var $diff;

  function __construct($file){
    $this->GetName($file);
  }

  //function testing only parser
  function ParseOnly($file, $parser, $jexamxml, $jexamcnfg){
    $this->Parser($file, $parser);
    $this->expectedparseresult = file_get_contents("$file->name.rc");

    if ($this->expectedparseresult == $this->parseresult){

      if ($this->parseresult == 0){

        if($this->CheckXml($file, $jexamxml, $jexamcnfg)){
          $this->htmlout = HtmlGen::DiffDiv($this->name, $this->folder, $this->diff);
          $result = false;
        }else{
          $this->htmlout = HtmlGen::OkDiv($this->name, $this->folder);
          $result = true;
        }

      }else{
        $this->htmlout = HtmlGen::OkDiv($this->name, $this->folder);
        $result = true;
      }

    }else{
      $this->htmlout = HtmlGen::ErrDiv($this->name, $this->folder, "Expected $this->expectedparseresult, but return $this->parseresult");
      $result = false;
    }

    $this->DeleteTmpFiles($file);
    return $result;
  }

  //function testing only interpreter
  function InterpreterOnly($file,  $interpreter){
    $this->Interpreter($file, 'src', $interpreter);
    $this->expectedintresult = file_get_contents("$file->name.rc");

    if ($this->expectedintresult == $this->intresult){

      if ($this->intresult == 0){

        if($this->CheckIntOut($file)){
          $this->htmlout = HtmlGen::DiffDiv($this->name, $this->folder, $this->diff);
          $result = false;
        }else{
          $this->htmlout = HtmlGen::OkDiv($this->name, $this->folder);
          $result = true;
        }

      }else{
        $this->htmlout = HtmlGen::OkDiv($this->name, $this->folder);
        $result = true;
      }

    }else{
      $this->htmlout = HtmlGen::ErrDiv($this->name, $this->folder, "Expected $this->expectedintresult, but return $this->intresult");
      $result = false;
    }

    $this->DeleteTmpFiles($file);
    return $result;

  }

  //function testing both script
  function TestBoth($file, $parser, $interpreter, $jexamxml, $jexamcnfg){
    $this->Parser($file, $parser);
    $this->expectedresult = file_get_contents("$file->name.rc");

    if ($this->parseresult == 0){

      $this->Interpreter($file, 'xml', $interpreter);

      if ($this->expectedresult == $this->intresult){

        if ($this->intresult == 0){

          if($this->CheckIntOut($file)){
            $this->htmlout = HtmlGen::DiffDiv($this->name, $this->folder, $this->diff);
            $result = false;
          }else{
            $this->htmlout = HtmlGen::OkDiv($this->name, $this->folder);
            $result = true;
          }

        }else{
          $this->htmlout = HtmlGen::OkDiv($this->name, $this->folder);
          $result = true;
        }

      }else{
        $this->htmlout = HtmlGen::ErrDiv($this->name, $this->folder, "Expected $this->expectedresult, but interpret return $this->intresult");
        $result = false;
      }

    }else{

      if($this->expectedresult == $this->parseresult){
        $this->htmlout = HtmlGen::OkDiv($this->name, $this->folder);
        $result = true;
      }else{
        $this->htmlout = HtmlGen::ErrDiv($this->name, $this->folder, "Expected $this->expectedresult, but parse.php return $this->parseresult");
        $result = false;
      }

    }



    $this->DeleteTmpFiles($file);
    return $result;
  }

  //function get file name and dirname
  //used for html report
  private function GetName($file){
    $this->name = preg_replace('/^.*\//','',$file->name);
    $this->folder = preg_replace('/\/[^\/]*$/','',$file->name);
  }

  //function run parse script
  private function Parser($file, $parser){
    exec("php7.4 $parser <$file->name.src >$file->name.xml", $out, $this->parseresult);
  }

  //function run interpreter script
  private function Interpreter($file, $suff, $interpreter){
    exec("python3.8 $interpreter --source=$file->name.$suff <$file->name.in >$file->name.tmp", $out, $this->intresult);

  }

  //function chceck equality of two XML files
  private function CheckXml($file, $jexamxml, $jexamcnfg){
    exec("java -jar $jexamxml $file->name.out $file->name.xml $file->name.diff /D $jexamcnfg", $output , $result);

    if ($result == 2) {
      fwrite(STDERR, "There was some ERROR during call script jexamXML\n For more information abou error check $file->name.out.log file" . PHP_EOL);
      exit(99);
    }

    if($result == 1 && file_exists("$file->name.diff")) $this->DiffProces($file);

    return $result;
  }

  //function make diff of two files
  private function CheckIntOut($file){
    exec("diff $file->name.out $file->name.tmp >$file->name.diff", $output , $result);
    if($result == 1 && file_exists("$file->name.diff")) $this->DiffProces($file);

    return $result;
  }

  //function remake diff, for html report
  private function DiffProces($file){
    $content = file_get_contents("$file->name.diff");
    $content = preg_replace('/</', '&lt', $content);
    $content = preg_replace('/>/', '&gt', $content);
    $content = preg_replace('/\\n/', '<br>', $content);
    $this->diff = $content;
  }


  private function DeleteTmpFiles($file){
    if (file_exists("$file->name.xml")) unlink("$file->name.xml");
    if (file_exists("$file->name.tmp")) unlink("$file->name.tmp");
    if (file_exists("$file->name.diff")) unlink("$file->name.diff");
  }
}
?>
