# Drop all
```
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
```

# Delete above block
```
delete from event where extrinsic in (select id from extrinsic where block_number >= 1450);
delete from transfer where extrinsic in (select id from extrinsic where block_number >= 1450);
delete from balance where block_number >= 1450;
delete from extrinsic where block_number >= 1450;
delete from block where block_number >= 1450;
```