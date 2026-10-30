import 'package:flutter/foundation.dart';
import 'repositories.dart';

class AnalyzeMessageUseCase {
  final AIRepository ai;
  AnalyzeMessageUseCase(this.ai);
  Future<Json> call(String text) {
    if(text.trim().isEmpty || text.length>10000) throw Exception('Enter between 1 and 10,000 characters.');
    return ai.analyze(text.trim());
  }
}
class SubmitMessageViewModel extends ChangeNotifier {
  final AnalyzeMessageUseCase analyze;
  final OCRRepository ocr;
  final HistoryRepository history;
  bool busy=false;
  String? error;
  Json? result;
  SubmitMessageViewModel(this.analyze,this.ocr,this.history);
  Future<void> submit(String text,bool save) async {
    busy=true;error=null;result=null;notifyListeners();
    try {result=await analyze(text);if(save)await history.save(result!);}
    catch(e){error=e.toString().replaceFirst('Exception: ','');}
    finally{busy=false;notifyListeners();}
  }
  Future<String?> readImage() async {
    busy=true;error=null;notifyListeners();
    try{return await ocr.extract();}
    catch(e){error=e.toString().replaceFirst('Exception: ','');return null;}
    finally{busy=false;notifyListeners();}
  }
  void clear(){result=null;error=null;notifyListeners();}
}
