// frontend/script.js
const API_URL = 'http://127.0.0.1:5000'; 
const outputDiv = document.getElementById('output');
const inputField = document.getElementById('command-input');

function printOutput(text, isError = false) {
    const p = document.createElement('div');
    p.className = isError ? 'error' : 'success';
    p.innerHTML = text.replace(/\n\n/g, '<br>').replace(/\n/g, '<br>'); 
    outputDiv.appendChild(p);
    outputDiv.scrollTop = outputDiv.scrollHeight; 
}

printOutput("Sanal İşletim Sistemi Başlatıldı.<br><br>Yardım için: 'help'");

async function handleCommand() {
    const commandLine = inputField.value.trim();
    if (!commandLine) return;
    
    printOutput(`<span class="command">CMD> ${commandLine}</span>`, false); 

    inputField.value = ''; 

    const parts = commandLine.split(/\s+/);
    const cmd = parts[0].toLowerCase();
    const args = parts.slice(1);
    
    let endpoint = null;
    let method = 'GET';
    let body = null;
    let requiredArgs = 0;

    switch (cmd) {
        case 'register':
            requiredArgs = 2; // id, şifre
            if (args.length === requiredArgs) {
                endpoint = '/register';
                method = 'POST';
                body = { user_id: args[0], password: args[1] };
            }
            break;
        case 'login':
            requiredArgs = 2; 
            if (args.length === requiredArgs) {
                endpoint = '/login';
                method = 'POST';
                body = { user_id: args[0], password: args[1] };
            }
            break;
        case 'create':
            requiredArgs = 2; 
            if (args.length === requiredArgs) {
                endpoint = '/create_file';
                method = 'POST';
                body = { size_mb: args[0], file_path: args[1] };
            }
            break;
        case 'write': 
            if (args.length >= 2) {
                endpoint = '/write_file';
                method = 'POST';
                const filePath = args[0];
                const contentText = args.slice(1).join(" "); 
                body = { file_path: filePath, content: contentText };
                requiredArgs = args.length; // Dinamik argüman sayısı
            } else { requiredArgs = 2; } // Hata mesajı için
            break;
        case 'cat': 
            requiredArgs = 1;
            if (args.length === requiredArgs) {
                endpoint = '/read_file';
                method = 'POST';
                body = { file_path: args[0] };
            }
            break;
        case 'run': 
            requiredArgs = 1;
            if (args.length === requiredArgs) {
                endpoint = '/execute_file';
                method = 'POST';
                body = { file_path: args[0] };
            }
            break;
        case 'delete':
            requiredArgs = 1; 
            if (args.length === requiredArgs) {
                endpoint = '/delete_file';
                method = 'POST';
                body = { file_path: args[0] };
            }
            break;
        case 'ls': endpoint = '/ls'; break;
        case 'status': endpoint = '/status'; break;
        
        // LOGOUT DÜZELTİLDİ: requiredArgs=0 olduğu için aşağıda onaylanacak
        case 'logout': endpoint = '/logout'; method = 'POST'; break;
        
        case 'list_users': endpoint = '/list_users'; break;
        case 'delete_user': 
            requiredArgs = 1;
            if (args.length === requiredArgs) {
                endpoint = '/delete_user/' + args[0]; 
                method = 'DELETE'; 
            }
            break;
        case 'set_quota': 
            requiredArgs = 2; 
            if (args.length === requiredArgs) {
                endpoint = '/set_quota';
                method = 'POST';
                body = { user_id: args[0], quota_mb: args[1] };
            }
            break;
            
        case 'help':
            printOutput("<b>Temel Komutlar:</b>\n" +
                        "  register <id> <şifre>      : Kayıt ol (100MB kota).\n" +
                        "  login <id> <şifre>         : Giriş yap.\n" +
                        "  logout                     : Çıkış yap.\n" +
                        "  create <MB> <yol>          : Dosya oluştur (Yazma İzni).\n" +
                        "  write <yol> <metin>        : Dosyaya metin ekle (Yazma İzni).\n" +
                        "  cat <yol>                  : Dosya oku (Okuma İzni).\n" +
                        "  run <yol>                  : Dosya çalıştır (Çalıştırma İzni - Engelli).\n" +
                        "  ls                         : Listele (Okuma İzni).\n" +
                        "  delete <yol>               : Sil (Yazma İzni).\n\n" +
                        "<b>Admin Komutları (login admin admin):</b>\n" +
                        "  list_users                 : Kullanıcıları listele.\n" +
                        "  delete_user <id>           : Kullanıcıyı sil.\n" +
                        "  set_quota <id> <MB>        : Kota güncelle.\n", false);
            return;
        default:
            printOutput(`Bilinmeyen komut: ${cmd}. Yardım için 'help' yazın.`, true);
            return;
    }
    
    // DÜZELTME BURADA YAPILDI:
    // Artık sadece "endpoint tanımlı mı" ve "argüman sayısı doğru mu" diye bakıyoruz.
    // Body'nin dolu olup olmaması logout'u etkilemeyecek.
    if (endpoint && args.length === requiredArgs) {
        try {
            const options = {
                method: method,
                headers: { 'Content-Type': 'application/json' },
            };
            if (body) {
                options.body = JSON.stringify(body);
            }
            
            const response = await fetch(API_URL + endpoint, options);
            const data = await response.json();
            
            printOutput(data.message, !data.success);
            
        } catch (error) {
            printOutput(`Ağ veya Sistem Hatası: API sunucusu çalışmıyor olabilir. (${error.message})`, true);
        }
    } else if (endpoint) {
        // Argüman sayısı tutmazsa buraya düşer
        printOutput(`HATA: '${cmd}' komutu için ${requiredArgs} argüman gerekli.`, true);
    }
}