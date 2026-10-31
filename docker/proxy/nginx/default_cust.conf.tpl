server {
    listen 80;
    server_name apiems.oneapp.ph www.apiems.oneapp.ph;

    location /.well-known/acme-challenge/ {
        root /vol/www/;
    }

    location / {
        return 301 https://;
    }
}

server {
    listen      443 ssl;
    server_name apiems.oneapp.ph www.apiems.oneapp.ph;

    ssl_certificate     /etc/letsencrypt/live/apiems.oneapp.ph/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/apiems.oneapp.ph/privkey.pem;

    include     /etc/nginx/options-ssl-nginx.conf;
    ssl_dhparam /vol/proxy/ssl-dhparams.pem;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location /static {
        alias /vol/static;
    }

    location /media {
        alias /uploads/media;
    }

    location /ws/ {          
        proxy_pass http://web:9000;
        proxy_http_version 1.1;    
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade"; 
        proxy_set_header Host $host;           
   }                                           
                                               
    location / {                               
        uwsgi_pass           app:9000;         
        include              /etc/nginx/uwsgi_params;
        client_max_body_size 10M;                    
    }                                                
}