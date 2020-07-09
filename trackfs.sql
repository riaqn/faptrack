CREATE TABLE videos (
    vid INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
   view_time INT NOT NULL DEFAULT 0,
   view_count INT NOT NULL DEFAULT 0,
   avg_view_time FLOAT AS (case view_count when 0 then 9e9999
                                            else CAST(view_time as FLOAT) / view_count
                            end
   ),
   avg_avg_view_time FLOAT AS (case view_count when 0 then 9e9999
                                               else avg_view_time / view_count
                                end
   )
);
