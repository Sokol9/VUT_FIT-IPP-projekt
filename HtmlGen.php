<?php
#########################
//implementation of HtmlGen.php used for test.php script from task no.2 from IPP
//autor: Jakub Sokolik (xsokol14)
//13.3.2021
#########################
class HtmlGen{

  public static function OkDiv($name, $folder){
    return "<div class=\"OkDiv\"><span class=\"name\">$name</span><span class=\"folder\"> in $folder</span></div>
    ";
  }

  public static function ErrDiv($name, $folder, $err){
    return "<div class=\"FailDiv\"><span class=\"name\">$name</span><span class=\"folder\"> in $folder</span><br><span class=\"expect\">$err<span></div>
    ";
  }

  public static function DiffDiv($name, $folder, $diff){
    return "<div class=\"FailDiv\"><span class=\"name\">$name</span><span class=\"folder\"> in $folder</span><br><p class=\"diff\">$diff</p></div>
    ";
  }

  public static function BuildHead(){
    return "<!DOCTYPE html>
    <html lang=\"en\">
      <head>
        <meta charset=\"utf-8\">
        <title>Test result for IPP</title>
        <style>
          body{padding: 0 5px 0 5px; font-family: sans-serif;}
          h1{margin: 5px 0 5px 0;}
          hr{border: none; border-top: 4px solid #284FA8;}
          dl{overflow: hidden;}
          dt{float:left;}
          dd{float:left; margin-left: 20px; color: #284FA8;}
          div{overflow: inherit;}
          div.header{text-align: center; font-style: italic;}
          div.OkDiv{background-color: #A7FC9D;}
          div.FailDiv{background-color: lightpink;}
          div.stats{font-weight: bold;}
          p.diff{margin: 0; padding-left: 40px; font-size: 13px;}
          span{font-size: 17px; font-weight: bold;}
          span.expect{padding-left: 40px; font-size: 13px;}
          span.folder{font-size: 13px; padding-left: 10px;}
        </style>
      </head>
      <body>
      ";
  }

  public static function GetHtml($pass, $fail, $htmlpass, $htmlfail){
    $total = $pass + $fail;
    $percentage = 0;
    if ($total >0) $percentage = round($pass/$total, 2)*100;
    //$file = fopen("index.html", 'w+');
    echo(HtmlGen::BuildHead());
    echo("<div class=\"header\"><h1>IPP 2020/2021 - test report</h1></div>
    <hr>
    <div class=\"stats\"><dl><div><dt>test passed:</dt><dd>$pass/$total</dd></div><div><dt>percentage:</dt><dd>$percentage%</dd></div></div>
    <hr>
    ");
    echo($htmlfail);
    echo($htmlpass);
    echo("</body>
    </html>");
    //fclose($file);
  }
}
 ?>
