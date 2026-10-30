import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:image_picker/image_picker.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';

typedef Json = Map<String, dynamic>;
abstract class AIRepository { Future<Json> analyze(String text); }
abstract class ScamRepository { Future<List<Json>> reports({String query = ''}); }
abstract class OCRRepository { Future<String?> extract(); }
abstract class HistoryRepository {
  Future<List<Json>> load();
  Future<void> save(Json result);
  Future<void> delete(String id);
}
class ApiRepository implements AIRepository, ScamRepository {
  final String baseUrl;
  final http.Client client;
  String? token;
  Json? account;
  final secure = const FlutterSecureStorage();
  ApiRepository(this.baseUrl, {http.Client? client}) : client = client ?? http.Client();
  Future<dynamic> request(String path, {Json? body}) async {
    final uri = Uri.parse('$baseUrl$path');
    final headers = {'Content-Type': 'application/json', if(token != null) 'Authorization': 'Bearer $token'};
    try {
      final response = await (body == null ? client.get(uri, headers: headers) : client.post(uri, headers: headers, body: jsonEncode(body))).timeout(const Duration(seconds: 15));
      final data = jsonDecode(response.body);
      if (response.statusCode >= 400) {
        final detail = data['detail'];
        throw Exception(detail is String ? detail : 'Check your input and try again.');
      }
      return data;
    } on SocketException { throw Exception('Cannot connect. Check your connection and server address.'); }
  }
  Future<void> signIn(String username, String password, bool register) async {
    account = Map<String,dynamic>.from(await request(register ? '/register' : '/login', body: {'username': username, 'password': password}));
    token = account!['token'];
    await secure.write(key: 'session', value: jsonEncode(account));
  }
  Future<void> restore() async {
    final value = await secure.read(key: 'session');
    if(value != null) { account = Map<String,dynamic>.from(jsonDecode(value)); token = account!['token']; }
  }
  Future<void> signOut() async {
    try { await request('/logout', body: {}); } finally { token=null; account=null; await secure.delete(key:'session'); }
  }
  @override Future<Json> analyze(String text) async => Map<String,dynamic>.from(await request('/analyse',body:{'text':text}));
  @override Future<List<Json>> reports({String query=''}) async => (await request('/reports?q=${Uri.encodeComponent(query)}') as List).map((r)=>Map<String,dynamic>.from(r)).toList();
}
class DeviceOCRRepository implements OCRRepository {
  @override Future<String?> extract() async {
    final picked = await ImagePicker().pickImage(source: ImageSource.gallery);
    if (picked == null) return null;
    final recognizer = TextRecognizer(script: TextRecognitionScript.latin);
    // image_picker gives a temporary cache copy, never delete the user's original.
    try {
      if(await picked.length()>8*1024*1024) throw Exception('Please choose an image smaller than 8 MB.');
      final result = await recognizer.processImage(InputImage.fromFilePath(picked.path));
      if(result.text.trim().isEmpty) throw Exception('No readable text. Try a clearer image or paste the message.');
      return result.text;
    } finally {
      await recognizer.close();
      final file=File(picked.path);
      if(await file.exists()) await file.delete();
    }
  }
}
class LocalHistoryRepository implements HistoryRepository {
  @override Future<List<Json>> load() async {
    final p=await SharedPreferences.getInstance();
    return (jsonDecode(p.getString('history') ?? '[]') as List).map((r)=>Map<String,dynamic>.from(r)).toList();
  }
  @override Future<void> save(Json result) async {
    final list=await load();
    list.removeWhere((r)=>r['id']==result['id']);list.insert(0,result);
    final p=await SharedPreferences.getInstance();await p.setString('history',jsonEncode(list));
  }
  @override Future<void> delete(String id) async {
    final list=await load();list.removeWhere((r)=>r['id']==id);
    final p=await SharedPreferences.getInstance();await p.setString('history',jsonEncode(list));
  }
}
String redact(String text) => text.replaceAll(RegExp(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}',caseSensitive:false),'[email removed]').replaceAll(RegExp(r'(?:\+?\d[\d ()-]{7,}\d)'),'[number removed]');
